"""Plumbing tests with the offline mock LLM. They prove the loop, retries, logs and memory work.
They do NOT prove that a real model writes or judges well: run the real pipeline for that."""
import json
from pathlib import Path

import pytest

from lesson_agent.config import load_settings
from lesson_agent.evaluator import evaluate
from lesson_agent.graph import Pipeline
from lesson_agent.llm import BaseLLM
from lesson_agent.memory import Memory
from lesson_agent.rubric import load_facts, load_rubric

FIX = Path(__file__).resolve().parent.parent / "fixtures"
TOPIC = "Introduction to RAG"


def make(tmp_path, mode="improve", retries=2):
    s = load_settings(provider="mock", memory_dir=tmp_path / "mem", output_dir=tmp_path / "out",
                      max_retries=retries, mock_mode=mode)
    return Pipeline(s, log=None), s


def test_bad_first_draft_is_rejected_then_fixed(tmp_path):
    p, s = make(tmp_path, "improve")
    st = p.run(TOPIC)
    assert st["status"] == "shipped"
    assert st["attempt"] == 2
    log = json.loads((Path(st["out_dir"]) / "rejection_log.json").read_text())
    assert [a["passed"] for a in log["attempts"]] == [False, True]
    assert log["attempts"][0]["changes_on_retry"], "the log must say what changed on the retry"
    assert (Path(st["out_dir"]) / "rejection_log.md").exists()
    assert (Path(st["out_dir"]) / "lesson.md").exists()


def test_good_first_draft_ships_with_no_rejections(tmp_path):
    p, _ = make(tmp_path, "perfect")
    st = p.run(TOPIC)
    assert st["status"] == "shipped" and st["attempt"] == 1


@pytest.mark.parametrize("retries", [1, 2])
def test_loop_always_terminates_and_flags_for_a_human(tmp_path, retries):
    p, _ = make(tmp_path, "never_improve", retries)
    st = p.run(TOPIC)
    assert st["attempt"] == 1 + retries
    assert st["status"] == "needs_human_review"
    out = Path(st["out_dir"])
    assert (out / "lesson.DRAFT_needs_human_review.md").exists()
    assert not (out / "lesson.md").exists(), "a failing lesson must never be saved as the shipped lesson"


def test_max_retries_is_clamped_to_two(tmp_path):
    s = load_settings(provider="mock", memory_dir=tmp_path, output_dir=tmp_path, max_retries=9)
    assert s.max_retries == 2


@pytest.mark.parametrize("name,check", [("subtle_fact", "accurate_grounded"), ("wrong_origin", "accurate_grounded"),
                                         ("no_example", "teaches_by_example"), ("misconception", "no_known_misconceptions")])
def test_deliberate_error_is_caught_and_repaired(tmp_path, name, check):
    p, _ = make(tmp_path, "perfect")
    st = p.run(TOPIC, tamper=name)
    first = st["history"][0]
    assert first["passed"] is False and first["tampered"] is True
    assert check in [c["id"] for c in first["checks"] if not c["passed"]]
    assert st["status"] == "shipped" and st["attempt"] == 2


def test_tampered_runs_are_not_learned_from(tmp_path):
    p, s = make(tmp_path, "perfect")
    for _ in range(3):
        p.run(TOPIC, tamper="misconception")
    assert Memory(s.memory_dir).active_guidelines() == []


def test_repeated_real_failures_create_a_guideline(tmp_path):
    p, s = make(tmp_path, "improve")  # weak first draft every time: a real, repeated failure
    p.run(TOPIC)
    p.run(TOPIC)
    mem = Memory(s.memory_dir)
    checks = {g["check"] for g in mem.active_guidelines()}
    assert "reading_level" in checks and "jargon_defined" in checks
    assert mem.guidelines_version() > 0


def test_learned_guidelines_reach_the_next_writer_prompt(tmp_path):
    p, s = make(tmp_path, "improve")
    p.run(TOPIC)
    p.run(TOPIC)
    seen = []
    original = p.gen_llm.complete
    p.gen_llm.complete = lambda system, user, **k: (seen.append(system), original(system, user, **k))[1]
    p2 = Pipeline(s, log=None)
    p2.gen_llm.complete = p.gen_llm.complete
    p2.run(TOPIC)
    assert "LESSONS LEARNED" in seen[0] and "Keep most sentences under 15 words" in seen[0]


def test_human_feedback_is_learned_immediately(tmp_path):
    p, s = make(tmp_path, "perfect")
    mem = Memory(s.memory_dir)
    mem.add_feedback("Use a food example, not an exam example.", check="audience_fit")
    p.run(TOPIC)
    g = mem.guideline_for("audience_fit")
    assert g and g["source"] == "human"
    assert mem.pending_feedback() == []


def test_the_rubric_is_never_edited_by_the_loop(tmp_path):
    before = (Path(__file__).resolve().parent.parent / "rubric.yaml").read_bytes()
    p, _ = make(tmp_path, "improve")
    for _ in range(5):
        p.run(TOPIC)
    after = (Path(__file__).resolve().parent.parent / "rubric.yaml").read_bytes()
    assert before == after


class _Garbage(BaseLLM):
    def complete(self, *a, **k):
        return "I think the lesson is great! Nothing to report."


class _AllPass(BaseLLM):
    def complete(self, *a, **k):
        return json.dumps({"checks": [{"id": i, "verdict": "PASS", "evidence": "", "reason": "ok", "fix": ""}
                                      for i in ("accurate_grounded", "covers_key_points", "teaches_by_example",
                                                "coherent_flow", "audience_fit")]})


def test_unreadable_judge_output_fails_closed():
    rubric, facts = load_rubric(), load_facts()
    res = evaluate((FIX / "reference_lesson.md").read_text(), rubric, facts, _Garbage())
    llm_results = [c for c in res.checks if c.kind == "llm"]
    assert llm_results and all(not c.passed for c in llm_results)
    assert not res.passed


def test_a_lenient_judge_cannot_rescue_a_lesson_that_code_rejects():
    rubric, facts = load_rubric(), load_facts()
    res = evaluate((FIX / "weak_draft.md").read_text(), rubric, facts, _AllPass())
    assert not res.passed
    assert {c.id for c in res.failed if c.kind == "code"}


def test_judge_missing_a_check_fails_closed():
    class Partial(BaseLLM):
        def complete(self, *a, **k):
            return json.dumps({"checks": [{"id": "accurate_grounded", "verdict": "PASS", "evidence": "", "reason": "ok", "fix": ""}]})
    res = evaluate((FIX / "reference_lesson.md").read_text(), load_rubric(), load_facts(), Partial())
    assert {c.id for c in res.failed} == {"covers_key_points", "teaches_by_example", "coherent_flow", "audience_fit"}
