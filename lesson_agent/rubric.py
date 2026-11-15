from __future__ import annotations

from pathlib import Path

import yaml

from .config import ROOT


class _Safe(dict):
    def __missing__(self, key):  # leave unknown {placeholders} untouched
        return "{" + key + "}"


def load_rubric(path: Path | str | None = None) -> dict:
    p = Path(path) if path else ROOT / "rubric.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def load_facts(path: Path | str | None = None) -> dict:
    p = Path(path) if path else ROOT / "knowledge" / "rag_facts.yaml"
    if not p.exists():
        raise FileNotFoundError(
            f"Fact sheet not found: {p}. Every topic needs a short, human-reviewed ground-truth file "
            "(see knowledge/rag_facts.yaml). The evaluator can only check accuracy against something."
        )
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _flat_thresholds(rubric: dict) -> dict:
    flat: dict = {}
    for group in rubric.get("thresholds", {}).values():
        flat.update(group)
    return flat


def check_text(check: dict, rubric: dict) -> str:
    return " ".join(str(check["pass_if"]).split()).format_map(_Safe(_flat_thresholds(rubric)))


def llm_checks(rubric: dict) -> list[dict]:
    return [c for c in rubric["checks"] if c["kind"] == "llm"]


def code_checks(rubric: dict) -> list[dict]:
    return [c for c in rubric["checks"] if c["kind"] == "code"]


def check_by_id(rubric: dict, cid: str) -> dict | None:
    return next((c for c in rubric["checks"] if c["id"] == cid), None)


def checklist_text(rubric: dict) -> str:
    return "\n".join(f"- [{c['id']}] {c['title']}: {check_text(c, rubric)}" for c in rubric["checks"])


def sections_text(rubric: dict, short: str) -> str:
    return "\n".join(
        f"  {i}. {s['label'].format_map(_Safe({'topic': short}))}"
        for i, s in enumerate(rubric["required_sections"], 1)
    )


def facts_text(facts: dict) -> str:
    lines = [f"Topic: {facts['topic']}"]
    lines += [f"- {f}" for f in facts["facts"]]
    return "\n".join(lines)


def mistakes_text(facts: dict) -> str:
    return "\n".join(f"- {m}" for m in facts.get("common_mistakes", [])) or "- (none listed)"
