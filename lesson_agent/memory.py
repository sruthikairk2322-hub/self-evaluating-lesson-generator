"""Persistent memory. Plain files on disk so a human can read, diff and edit them.

memory/
  guidelines.json        learned writing guidelines, injected into the generator prompt
  run_history.jsonl      one line per real run (what failed, what shipped)
  human_feedback.jsonl   notes from a human reviewer, consumed by `evolve`
  rubric_proposals.md    suggestions to change the rubric: a HUMAN decides, the code never applies them
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

MAX_GUIDELINES = 15  # one per rubric check (11) plus a few "general" notes from humans


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Memory:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.g_path = self.root / "guidelines.json"
        self.runs_path = self.root / "run_history.jsonl"
        self.fb_path = self.root / "human_feedback.jsonl"
        self.prop_path = self.root / "rubric_proposals.md"

    # ---------------------------------------------------------- guidelines
    def _gdoc(self) -> dict:
        if self.g_path.exists():
            return json.loads(self.g_path.read_text(encoding="utf-8"))
        return {"version": 0, "items": []}

    def active_guidelines(self) -> list[dict]:
        return self._gdoc()["items"]

    def guidelines_version(self) -> int:
        return self._gdoc()["version"]

    def guideline_for(self, check_id: str) -> dict | None:
        return next((g for g in self.active_guidelines() if g["check"] == check_id), None)

    def upsert_guideline(self, check_id: str, text: str, source: str, seq: int) -> None:
        doc = self._gdoc()
        existing = next((g for g in doc["items"] if g["check"] == check_id), None)
        if existing:
            existing.update(text=text, updated=_now(), updated_seq=seq, source=source,
                            revisions=existing.get("revisions", 1) + 1)
        else:
            doc["items"].append({"check": check_id, "text": text, "created": _now(), "updated": _now(),
                                 "updated_seq": seq, "source": source, "revisions": 1})
        if len(doc["items"]) > MAX_GUIDELINES:  # keep the prompt short: drop the stalest
            doc["items"].sort(key=lambda g: g["updated_seq"])
            doc["items"] = doc["items"][-MAX_GUIDELINES:]
        doc["version"] += 1
        self.g_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------------------------------------------------------- run history
    def runs(self) -> list[dict]:
        if not self.runs_path.exists():
            return []
        return [json.loads(ln) for ln in self.runs_path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def next_seq(self) -> int:
        return len(self.runs()) + 1

    def record_run(self, summary: dict) -> int:
        summary = dict(summary)
        summary["seq"] = self.next_seq()
        with self.runs_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        return summary["seq"]

    # ---------------------------------------------------------- human feedback
    def add_feedback(self, text: str, check: str | None = None) -> None:
        with self.fb_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now(), "check": check, "text": text, "used": False}, ensure_ascii=False) + "\n")

    def _feedback(self) -> list[dict]:
        if not self.fb_path.exists():
            return []
        return [json.loads(ln) for ln in self.fb_path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def pending_feedback(self) -> list[dict]:
        return [f for f in self._feedback() if not f["used"]]

    def mark_feedback_used(self) -> None:
        items = self._feedback()
        for f in items:
            f["used"] = True
        self.fb_path.write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in items) + ("\n" if items else ""),
                                encoding="utf-8")

    # ---------------------------------------------------------- rubric proposals
    def add_proposal(self, check_id: str, body: str, rubric_version: int) -> bool:
        marker = f"<!-- {check_id}@rubric-v{rubric_version} -->"
        existing = self.prop_path.read_text(encoding="utf-8") if self.prop_path.exists() else "# Rubric proposals (for a human to review)\n"
        if marker in existing:
            return False
        self.prop_path.write_text(existing.rstrip() + f"\n\n{marker}\n## {check_id}\n{body}\n", encoding="utf-8")
        return True
