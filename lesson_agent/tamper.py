"""Deliberate error injection, for the demo video and for testing the evaluator.

Each tamper edits a good draft in a known way, so we can prove the evaluator catches it.
Runs with a tamper are marked synthetic and are NEVER used for learning (see evolve.py).
"""
from __future__ import annotations

import re

TAMPERS: dict[str, dict] = {
    "wrong_origin": {
        "sentence": "RAG was invented by Google engineers in 2017.",
        "expect": "no_known_misconceptions (code) and accurate_grounded (judge)",
    },
    "misconception": {
        "sentence": "RAG works by retraining the LLM on your documents every night, so the LLM changes its weights.",
        "expect": "no_known_misconceptions (code) and accurate_grounded (judge)",
    },
    "subtle_fact": {
        "sentence": "In the Retrieve step, the LLM looks for the answer inside its own memory, so no database or documents are needed.",
        "heading": r"^##\s+how",  # inserted late, after the terms are defined, so only the judge can notice
        "expect": "accurate_grounded (judge only: no regex can catch this one)",
    },
    "jargon": {
        "sentence": "Under the hood, the system measures cosine similarity between high-dimensional vectors in a latent space.",
        "expect": "jargon_defined and plain_words (code), audience_fit (judge)",
    },
    "no_example": {
        "sentence": None,
        "expect": "structure (code) and teaches_by_example (judge)",
    },
}


def describe(name: str) -> str:
    return TAMPERS[name]["expect"]


def apply(lesson: str, name: str) -> str:
    if name not in TAMPERS:
        raise ValueError(f"Unknown tamper '{name}'. Choose from: {', '.join(TAMPERS)}")
    if name == "no_example":
        return _remove_example_section(lesson)
    t = TAMPERS[name]
    return _insert_sentence(lesson, t["sentence"], t.get("heading", r"^##\s+what is"))


def _insert_sentence(lesson: str, sentence: str, heading: str = r"^##\s+what is") -> str:
    lines = lesson.splitlines()
    h = next((i for i, ln in enumerate(lines) if re.match(heading, ln, re.I)), None)
    if h is None:
        return lesson.rstrip() + "\n\n" + sentence + "\n"
    i = h + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i + 1 < len(lines) and lines[i + 1].strip():  # end of the first paragraph
        i += 1
    if i >= len(lines):
        return lesson.rstrip() + "\n\n" + sentence + "\n"
    lines[i] = lines[i].rstrip() + " " + sentence
    return "\n".join(lines) + "\n"


def _remove_example_section(lesson: str) -> str:
    out, skipping = [], False
    for ln in lesson.splitlines():
        if re.match(r"^##\s", ln):
            skipping = bool(re.search(r"example", ln, re.I))
        if not skipping:
            out.append(ln)
    return "\n".join(out) + "\n"
