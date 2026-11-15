"""Offline stand-in for an LLM, so the *plumbing* (graph, retries, logs, memory) can be tested without an API key.

IMPORTANT: this proves the loop works. It is NOT evidence that any real model writes or judges well.
The mock writer returns a deliberately weak draft first, then a good lesson after it receives feedback.
The mock judge uses simple keyword rules.
"""
from __future__ import annotations

import json
import re

from .config import ROOT
from .llm import BaseLLM

_NEG = re.compile(r"\b(not|never|no|without|cannot|unlike|instead|rather|different)\b|n['’]t", re.I)


def _fixture(name: str) -> str:
    return (ROOT / "fixtures" / name).read_text(encoding="utf-8")


class MockLLM(BaseLLM):
    name = "mock"

    def __init__(self, role: str, mode: str = "improve"):
        self.role = role
        self.mode = mode

    def complete(self, system, user, temperature=0.0, max_tokens=4000):
        if self.role == "generator":
            return self._write(user)
        if self.role == "evaluator":
            return self._judge(user)
        return self._evolve(user)

    # ------------------------------------------------------------- writer
    def _write(self, user: str) -> str:
        retry = "### RETRY" in user
        good = _fixture("reference_lesson.md")
        weak = _fixture("weak_draft.md")
        if self.mode == "perfect":
            return good + "\n===CHANGES===\n- " + ("Rewrote to fix the failed checks." if retry else "First draft.")
        if self.mode == "never_improve":
            return weak + "\n===CHANGES===\n- Tried again but changed almost nothing."
        if not retry:
            return weak + "\n===CHANGES===\n- First draft."
        return good + (
            "\n===CHANGES===\n"
            "- Rewrote every sentence to be short and use everyday words.\n"
            "- Added the missing sections: A full example and Quick recap.\n"
            "- Explained each technical word the first time it appears.\n"
            "- Removed idioms and the false claims about retraining."
        )

    # ------------------------------------------------------------- judge
    def _judge(self, user: str) -> str:
        lesson = re.search(r"<lesson>\n(.*)\n</lesson>", user, re.S).group(1)
        sents = re.split(r"(?<=[.!?])\s+", lesson.replace("\n", " "))

        def find(pat: str, skip_neg: bool = False):
            for s in sents:
                if re.search(pat, s, re.I) and not (skip_neg and _NEG.search(s)):
                    return s
            return None

        out = []

        def add(cid, ok, reason_ok, reason_bad, evidence="", fix=""):
            out.append({"id": cid, "verdict": "PASS" if ok else "FAIL", "evidence": "" if ok else evidence[:200],
                        "reason": reason_ok if ok else reason_bad, "fix": "" if ok else fix})

        bad = (find(r"\b(invent|introduc|creat)\w*\b[^.]*\b(Google|OpenAI|Microsoft)\b")
               or find(r"\b(retrain|retrains|retraining)\b[^.]*\b(model|LLM)", True)
               or find(r"guarantee|\b100\s?%", True)
               or find(r"own memory|no database"))
        add("accurate_grounded", bad is None, "Claims match the ground truth.",
            "A claim contradicts the ground truth.", bad or "", "Rewrite the sentence so it matches the ground truth, or delete it.")

        need = {"retriev": "retrieve step", "augment": "augment step", "generat": "generate step", "prompt": "prompt",
                "chunk": "chunks", "embedding": "embeddings", "hallucinat": "hallucination",
                r"out of date|outdated": "out-of-date knowledge", "private": "private data",
                r"not magic|cannot do|limit|mistake": "a limit of RAG"}
        missing = [name for pat, name in need.items() if not re.search(pat, lesson, re.I)]
        add("covers_key_points", not missing, "What, why, how and a limit are all explained.",
            "Missing key points: " + ", ".join(missing) + ".", "", "Add the missing key points and explain each in 2-3 short sentences.")

        ex = re.search(r"^##\s+[^\n]*example[^\n]*\n(.*?)(?=^##\s|\Z)", lesson, re.I | re.S | re.M)
        ok_ex = bool(ex) and len(ex.group(1).split()) > 60 and all(w in ex.group(1) for w in ("Retrieve", "Augment", "Generate")) and '"' in ex.group(1)
        add("teaches_by_example", ok_ex, "A worked example shows all three steps with sample text.",
            "There is no worked example that shows retrieve, augment and generate with sample text.", "",
            "Add a concrete worked example with real sample text for each step.")

        heads = [h.lower() for h in re.findall(r"^##\s+(.*)$", lesson, re.M)]
        def idx(p): return next((i for i, h in enumerate(heads) if re.search(p, h)), None)
        order = [idx(p) for p in (r"^what is", r"^why", r"^how", r"example", r"recap|summary")]
        ok_flow = None not in order and order == sorted(order)
        add("coherent_flow", ok_flow, "Sections build on each other in a clear order.",
            "The sections are missing or out of order, so the learner has to jump ahead.", "",
            "Put the sections in the order what, why, how, example, recap.")

        talk = find(r"\b(obviously|simply|easy|easily|trivial|clearly|of course)\b")
        add("audience_fit", talk is None, "Simple words and a friendly tone for a beginner.",
            "Talking-down words or hard wording make this hard for the learner.", talk or "",
            "Use simple words and remove talking-down words.")
        return json.dumps({"checks": out})

    # ------------------------------------------------------------- evolver
    def _evolve(self, user: str) -> str:
        m = re.search(r"^FIX_HINT:\s*(.*)$", user, re.M)
        fb = re.search(r"HUMAN FEEDBACK \(may be empty\):\n- (.*)", user)
        fb_text = fb.group(1).strip() if fb else ""
        if fb_text and fb_text != "(none)":
            return fb_text  # a human's note is the strongest signal
        hint = m.group(1).strip() if m else ""
        return hint or "Keep sentences short and explain every new word."
