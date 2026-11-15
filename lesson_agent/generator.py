from __future__ import annotations

import re

from .config import ROOT
from .llm import BaseLLM
from .rubric import checklist_text, facts_text, mistakes_text, sections_text

CHANGES_MARK = "===CHANGES==="


def build_system(topic: str, rubric: dict, facts: dict, guidelines: list[dict]) -> str:
    template = (ROOT / "prompts" / "generator.md").read_text(encoding="utf-8")
    short = facts.get("short_name", topic)
    g_txt = "\n".join(f"- {g['text']}" for g in guidelines) or "- (none yet)"
    return (
        template.replace("<<TOPIC>>", topic)
        .replace("<<AUDIENCE>>", " ".join(rubric["audience"].split()))
        .replace("<<FACTS>>", facts_text(facts))
        .replace("<<MISTAKES>>", mistakes_text(facts))
        .replace("<<CHECKLIST>>", checklist_text(rubric))
        .replace("<<GUIDELINES>>", g_txt)
        .replace("<<SECTIONS>>", sections_text(rubric, short))
        .replace("<<SHORT>>", short)
    )


def feedback_text(failed: list[dict]) -> str:
    lines = []
    for c in failed:
        ev = f' | quoted from your draft: "{c["evidence"]}"' if c.get("evidence") else ""
        lines.append(f"- [{c['id']}] {c['reason']}{ev} | FIX: {c['fix']}")
    return "\n".join(lines)


def build_user(attempt: int, previous: str | None, failed: list[dict] | None) -> str:
    if attempt == 1 or not previous:
        return "### FIRST DRAFT\nWrite the lesson now."
    return (
        f"### RETRY (attempt {attempt})\n"
        "Your previous draft was REJECTED by the quality reviewer.\n\n"
        f"PREVIOUS DRAFT:\n<draft>\n{previous}\n</draft>\n\n"
        f"FAILED CHECKS (fix every one):\n{feedback_text(failed or [])}\n\n"
        "Rewrite the lesson. Keep every part that already passed unchanged where you can. "
        "Output the full lesson, then the line ===CHANGES===, then a bullet list of exactly what you changed."
    )


def parse_output(raw: str) -> tuple[str, list[str]]:
    raw = raw.strip()
    fence = re.match(r"^```(?:markdown|md)?\s*\n(.*)\n```\s*$", raw, re.S)
    if fence:
        raw = fence.group(1).strip()
    if CHANGES_MARK in raw:
        lesson, ch = raw.split(CHANGES_MARK, 1)
    else:
        lesson, ch = raw, ""
    changes = [re.sub(r"^[-*•]\s*", "", ln.strip()) for ln in ch.splitlines() if ln.strip()]
    return lesson.strip() + "\n", changes


def generate(
    llm: BaseLLM,
    topic: str,
    rubric: dict,
    facts: dict,
    guidelines: list[dict],
    attempt: int,
    previous: str | None = None,
    failed: list[dict] | None = None,
) -> tuple[str, list[str]]:
    system = build_system(topic, rubric, facts, guidelines)
    user = build_user(attempt, previous, failed)
    return parse_output(llm.complete(system, user, temperature=0.7, max_tokens=4000))
