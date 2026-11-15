from pathlib import Path

import pytest

from lesson_agent import tamper
from lesson_agent.deterministic import run_code_checks
from lesson_agent.rubric import load_facts, load_rubric

FIX = Path(__file__).resolve().parent.parent / "fixtures"
RUBRIC, FACTS = load_rubric(), load_facts()


def failed_ids(text: str) -> set[str]:
    return {c.id for c in run_code_checks(text, RUBRIC, FACTS) if not c.passed}


def test_reference_lesson_passes_every_code_check():
    assert failed_ids((FIX / "reference_lesson.md").read_text()) == set()


def test_weak_draft_fails_every_code_check():
    assert failed_ids((FIX / "weak_draft.md").read_text()) == {c["id"] for c in RUBRIC["checks"] if c["kind"] == "code"}


@pytest.mark.parametrize(
    "name,expected",
    [
        ("wrong_origin", {"no_known_misconceptions"}),
        ("misconception", {"no_known_misconceptions"}),
        ("jargon", {"jargon_defined", "plain_words"}),
        ("no_example", {"structure"}),
    ],
)
def test_each_tamper_is_caught_by_code(name, expected):
    good = (FIX / "reference_lesson.md").read_text()
    assert expected <= failed_ids(tamper.apply(good, name))


def test_subtle_fact_needs_the_llm_judge():
    """No regex can catch this one. That is the point: it proves why we need a judge as well as code."""
    good = (FIX / "reference_lesson.md").read_text()
    assert failed_ids(tamper.apply(good, "subtle_fact")) == set()


def test_negated_sentences_are_not_flagged():
    good = (FIX / "reference_lesson.md").read_text()
    text = good + "\nRAG does not retrain the LLM and it does not change its weights.\n"
    assert "no_known_misconceptions" not in failed_ids(text)


def test_unsupported_statistic_is_flagged():
    good = (FIX / "reference_lesson.md").read_text()
    assert "no_known_misconceptions" in failed_ids(good + "\nRAG cuts mistakes by 40%.\n")
