"""The evaluator = code checks + an LLM judge. Hard pass/fail, fails closed, never edits the lesson."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .config import ROOT
from .deterministic import CheckResult, run_code_checks
from .llm import BaseLLM
from .rubric import check_by_id, check_text, facts_text, llm_checks


@dataclass
class EvalResult:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "n_checks": len(self.checks),
            "n_failed": len(self.failed),
            "checks": [c.to_dict() for c in self.checks],
        }


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`>#]", "", s)).strip().lower()


def _extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        text = m.group(1)
    else:
        i, j = text.find("{"), text.rfind("}")
        if i != -1 and j > i:
            text = text[i : j + 1]
    return json.loads(text)


def _judge_prompts(lesson: str, rubric: dict, facts: dict) -> tuple[str, str]:
    template = (ROOT / "prompts" / "evaluator.md").read_text(encoding="utf-8")
    checks = llm_checks(rubric)
    checks_txt = "\n".join(f"- id: {c['id']}\n  title: {c['title']}\n  PASS only if: {check_text(c, rubric)}" for c in checks)
    system = (
        template.replace("<<AUDIENCE>>", " ".join(rubric["audience"].split()))
        .replace("<<FACTS>>", facts_text(facts))
        .replace("<<CHECKS>>", checks_txt)
        .replace("<<IDS>>", ", ".join(c["id"] for c in checks))
    )
    user = f"<lesson>\n{lesson}\n</lesson>"
    return system, user


def run_judge(lesson: str, rubric: dict, facts: dict, llm: BaseLLM) -> list[CheckResult]:
    system, user = _judge_prompts(lesson, rubric, facts)
    wanted = [c["id"] for c in llm_checks(rubric)]
    data = None
    last_err = ""
    for _ in range(2):  # one retry if the judge returns unreadable output
        raw = llm.complete(system, user, temperature=0.0, max_tokens=3000)
        try:
            data = _extract_json(raw)
            break
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
    results: list[CheckResult] = []
    by_id = {}
    if data and isinstance(data.get("checks"), list):
        by_id = {str(c.get("id")): c for c in data["checks"] if isinstance(c, dict)}
    for cid in wanted:
        item = by_id.get(cid)
        hint = check_by_id(rubric, cid)["fix_hint"]
        if item is None:  # FAIL CLOSED: no verdict means no pass
            reason = "The judge did not return a verdict for this check, so it counts as a fail."
            if data is None:
                reason = f"The judge's answer could not be read ({last_err[:80]}), so it counts as a fail."
            results.append(CheckResult(cid, False, reason, "", hint, kind="llm", evidence_verified=False))
            continue
        verdict = str(item.get("verdict", "")).strip().upper()
        passed = verdict == "PASS"  # anything other than a clear PASS is a FAIL
        evidence = str(item.get("evidence", "") or "")
        verified = (not evidence) or (_norm(evidence) in _norm(lesson))
        results.append(
            CheckResult(
                id=cid,
                passed=passed,
                reason=str(item.get("reason", "")).strip(),
                evidence=evidence[:300],
                fix="" if passed else (str(item.get("fix", "")).strip() or hint),
                kind="llm",
                evidence_verified=verified,
            )
        )
    return results


def evaluate(lesson: str, rubric: dict, facts: dict, judge_llm: BaseLLM) -> EvalResult:
    """Run BOTH layers every time, so one rejection lists every problem (fewer wasted retries)."""
    code = run_code_checks(lesson, rubric, facts)
    judged = run_judge(lesson, rubric, facts, judge_llm)
    order = {c["id"]: i for i, c in enumerate(rubric["checks"])}
    return EvalResult(sorted(code + judged, key=lambda c: order[c.id]))
