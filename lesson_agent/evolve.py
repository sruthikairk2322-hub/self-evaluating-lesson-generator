"""Self-evolution.

What may change by itself  : generator guidelines (small, reversible, versioned, visible in memory/).
What may NOT change itself : the rubric (the quality bar). The system only writes *proposals* for a human.
Why: if a system can edit its own bar, the easiest way to "improve" is to lower it.

Learning signals:
  * a check failing on the FIRST attempt in several real runs  -> the writer keeps making that mistake
  * a human reviewer's note (`python run.py feedback ...`)       -> learn immediately
Synthetic runs (deliberate error injection) are excluded: we do not learn from errors we planted.
"""
from __future__ import annotations

from typing import Callable

from .config import ROOT
from .llm import BaseLLM
from .memory import Memory
from .rubric import check_by_id, check_text

WINDOW = 10  # look at the last N real runs


def _clean(text: str) -> str:
    text = " ".join(text.strip().strip('"').split())
    if len(text) > 300:
        text = text[:300].rsplit(" ", 1)[0].rstrip(",;:") + "."
    return text


def _write_guideline(llm: BaseLLM, rubric: dict, check_id: str, failures: list[str], feedback: list[str],
                     existing: dict | None) -> str:
    check = check_by_id(rubric, check_id)
    if check is None:  # "general" human feedback
        check = {"id": check_id, "title": "General quality", "pass_if": "The lesson is good for the learner.", "fix_hint": ""}
        pass_if = check["pass_if"]
    else:
        pass_if = check_text(check, rubric)
    prompt = (
        (ROOT / "prompts" / "evolve.md").read_text(encoding="utf-8")
        .replace("<<CHECK_ID>>", check_id)
        .replace("<<CHECK_TITLE>>", check["title"])
        .replace("<<PASS_IF>>", pass_if)
        .replace("<<FAILURES>>", "\n".join(f"- {f}" for f in failures[-5:][::-1]) or "- (none)")
        .replace("<<FEEDBACK>>", "\n".join(f"- {f}" for f in feedback) or "- (none)")
        .replace("<<EXISTING>>", existing["text"] if existing else "(none)")
        .replace("<<FIX_HINT>>", check.get("fix_hint", "") or (feedback[0] if feedback else ""))
    )
    return _clean(llm.complete("You write short, precise writing guidelines.", prompt, temperature=0.3, max_tokens=200))


def maybe_evolve(memory: Memory, rubric: dict, llm: BaseLLM, threshold: int, log: Callable[[str], None] = print) -> list[str]:
    done: list[str] = []
    all_runs = memory.runs()
    seq_now = len(all_runs)
    real = [r for r in all_runs if not r.get("tampered")][-WINDOW:]

    # 1) human feedback: learn right away
    pending = memory.pending_feedback()
    if pending:
        by_check: dict[str, list[str]] = {}
        for fb in pending:
            by_check.setdefault(fb.get("check") or "general", []).append(fb["text"])
        for cid, notes in by_check.items():
            key = cid if check_by_id(rubric, cid) else f"general-{seq_now}"
            text = _write_guideline(llm, rubric, cid, [], notes, memory.guideline_for(key))
            if text:
                memory.upsert_guideline(key, text, source="human", seq=seq_now)
                done.append(key)
                log(f"  learned from human feedback [{key}]: {text}")
        memory.mark_feedback_used()

    # 2) repeated first-attempt failures
    for check in rubric["checks"]:
        cid = check["id"]
        g = memory.guideline_for(cid)
        since = g["updated_seq"] if g else 0
        fails = [r for r in real if r["seq"] > since and cid in r.get("first_attempt_failed", [])]
        if len(fails) >= threshold:
            reasons = [f"{r['first_attempt_details'].get(cid, {}).get('reason', '')}" for r in fails]
            text = _write_guideline(llm, rubric, cid, reasons, [], g)
            if text and (not g or text != g["text"]):
                memory.upsert_guideline(cid, text, source="failures", seq=seq_now)
                done.append(cid)
                log(f"  learned from {len(fails)} repeated failures [{cid}]: {text}")

    # 3) rubric proposals: humans decide, code never edits rubric.yaml
    if len(real) >= 4:
        for check in rubric["checks"]:
            cid = check["id"]
            rate = sum(cid in r.get("first_attempt_failed", []) for r in real) / len(real)
            if rate >= 0.5 and memory.guideline_for(cid):
                body = (
                    f"`{cid}` failed on the first attempt in {rate:.0%} of the last {len(real)} real runs even though "
                    f"a guideline exists. Either the writer prompt needs a bigger change, or the check is too strict "
                    f"or unclear. Please review the check text and recent reasons in memory/run_history.jsonl."
                )
                if memory.add_proposal(cid, body, rubric.get("version", 0)):
                    log(f"  wrote a rubric proposal for [{cid}] (needs a human)")
    return done
