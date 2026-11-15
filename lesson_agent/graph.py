"""The agentic loop, as a LangGraph state machine.

load_memory -> generate -> tamper -> evaluate --pass--------------------> finalize -> update_memory -> END
                  ^                     |
                  |                     +--fail & retries left--> reflect
                  +------------------------------------------------+
                                        +--fail & no retries left--> finalize (flagged for a human)

Loop control (retry or stop) is plain Python, never an LLM decision, so the loop always ends.
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
from pathlib import Path
from typing import Callable, TypedDict

from langgraph.graph import END, StateGraph

from . import generator, tamper as tamper_mod
from .config import Settings
from .evaluator import evaluate
from .evolve import maybe_evolve
from .llm import get_llm
from .memory import Memory
from .rubric import load_facts, load_rubric


class State(TypedDict, total=False):
    topic: str
    run_id: str
    out_dir: str
    attempt: int
    max_retries: int
    guidelines: list
    draft: str
    changes: list
    prev_draft: str
    feedback: list
    history: list
    tamper: str
    tampered: bool
    status: str
    final_lesson: str


class Pipeline:
    def __init__(self, settings: Settings, rubric: dict | None = None, facts: dict | None = None,
                 log: Callable[[str], None] | None = print):
        self.s = settings
        self.rubric = rubric or load_rubric()
        self.facts = facts or load_facts()
        self.memory = Memory(settings.memory_dir)
        self.gen_llm = get_llm(settings, "generator")
        self.eval_llm = get_llm(settings, "evaluator")
        self.evo_llm = get_llm(settings, "evolver")
        self.log = log or (lambda _m: None)
        self.graph = self._build()

    # ------------------------------------------------------------ graph
    def _build(self):
        g = StateGraph(State)
        g.add_node("load_memory", self.n_load_memory)
        g.add_node("generate", self.n_generate)
        g.add_node("tamper", self.n_tamper)
        g.add_node("evaluate", self.n_evaluate)
        g.add_node("reflect", self.n_reflect)
        g.add_node("finalize", self.n_finalize)
        g.add_node("update_memory", self.n_update_memory)
        g.set_entry_point("load_memory")
        g.add_edge("load_memory", "generate")
        g.add_edge("generate", "tamper")
        g.add_edge("tamper", "evaluate")
        g.add_conditional_edges("evaluate", self.route, {"retry": "reflect", "done": "finalize"})
        g.add_edge("reflect", "generate")
        g.add_edge("finalize", "update_memory")
        g.add_edge("update_memory", END)
        return g.compile()

    def run(self, topic: str, tamper: str | None = None) -> State:
        run_id = dt.datetime.now().strftime("run_%Y%m%d_%H%M%S")
        out = self.s.output_dir / run_id
        (out / "attempts").mkdir(parents=True, exist_ok=True)
        state: State = {"topic": topic, "run_id": run_id, "out_dir": str(out), "attempt": 0,
                        "max_retries": self.s.max_retries, "history": [], "tamper": tamper or "", "tampered": False}
        return self.graph.invoke(state, config={"recursion_limit": 60})

    # ------------------------------------------------------------ nodes
    def n_load_memory(self, st: State) -> dict:
        gl = self.memory.active_guidelines()
        self.log(f"\n=== {st['run_id']} | topic: {st['topic']} | provider: {self.s.provider} "
                 f"| up to {1 + st['max_retries']} attempts ===")
        self.log(f"Memory: {len(gl)} learned guideline(s) will be given to the writer "
                 f"(guidelines v{self.memory.guidelines_version()}).")
        return {"guidelines": gl}

    def n_generate(self, st: State) -> dict:
        attempt = st["attempt"] + 1
        self.log(f"\n[attempt {attempt}] Writing the lesson...")
        failed = st.get("feedback") or None
        lesson, changes = generator.generate(
            self.gen_llm, st["topic"], self.rubric, self.facts, st["guidelines"],
            attempt, previous=st.get("prev_draft"), failed=failed)
        out = Path(st["out_dir"])
        (out / "attempts" / f"attempt_{attempt}.md").write_text(lesson, encoding="utf-8")
        history = [dict(h) for h in st["history"]]
        if attempt > 1 and history:
            diff = list(difflib.unified_diff(st["prev_draft"].splitlines(), lesson.splitlines(), lineterm="", n=0))
            history[-1]["changes_on_retry"] = changes
            history[-1]["diff_lines"] = sum(1 for d in diff if d[:1] in "+-" and d[:3] not in ("+++", "---"))
            if changes:
                self.log("  What the writer says it changed: " + "; ".join(changes))
        return {"attempt": attempt, "draft": lesson, "changes": changes, "history": history}

    def n_tamper(self, st: State) -> dict:
        if st.get("tamper") and st["attempt"] == 1:
            self.log(f"  >> DELIBERATE ERROR injected ('{st['tamper']}'). Evaluator should catch: "
                     f"{tamper_mod.describe(st['tamper'])}")
            new = tamper_mod.apply(st["draft"], st["tamper"])
            (Path(st["out_dir"]) / "attempts" / "attempt_1_tampered.md").write_text(new, encoding="utf-8")
            return {"draft": new, "tampered": True}
        return {}

    def n_evaluate(self, st: State) -> dict:
        self.log(f"[attempt {st['attempt']}] Evaluating against the rubric (code checks + LLM judge)...")
        res = evaluate(st["draft"], self.rubric, self.facts, self.eval_llm)
        d = res.to_dict()
        out = Path(st["out_dir"])
        (out / "attempts" / f"evaluation_{st['attempt']}.json").write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        self.log(f"  {d['n_checks'] - d['n_failed']}/{d['n_checks']} checks passed -> {'PASS' if d['passed'] else 'REJECTED'}")
        for c in res.failed:
            ev = f'  evidence: "{c.evidence[:90]}"' if c.evidence else ""
            if c.evidence and not c.evidence_verified:
                ev += "  [WARNING: this quote was not found in the lesson]"
            self.log(f"   x {c.id} [{c.kind}]: {c.reason}{ev}")
        history = [dict(h) for h in st["history"]]
        history.append({"attempt": st["attempt"], "passed": d["passed"], "n_failed": d["n_failed"],
                        "checks": d["checks"], "tampered": bool(st.get("tampered")) and st["attempt"] == 1})
        return {"history": history}

    def route(self, st: State) -> str:
        if st["history"][-1]["passed"]:
            return "done"
        return "retry" if st["attempt"] <= st["max_retries"] else "done"

    def n_reflect(self, st: State) -> dict:
        failed = [c for c in st["history"][-1]["checks"] if not c["passed"]]
        self.log(f"[attempt {st['attempt']}] Rejected. Sending {len(failed)} reason(s) back to the writer for a retry.")
        return {"feedback": failed, "prev_draft": st["draft"]}

    def n_finalize(self, st: State) -> dict:
        hist = st["history"]
        last = hist[-1]
        out = Path(st["out_dir"])
        if last["passed"]:
            status, final_attempt = "shipped", last["attempt"]
        else:  # out of retries: keep the best attempt, but a human must look at it
            status = "needs_human_review"
            final_attempt = min(hist, key=lambda h: (h["n_failed"], -h["attempt"]))["attempt"]
        if final_attempt == last["attempt"]:
            final_text = st["draft"]
        else:
            final_text = (out / "attempts" / f"attempt_{final_attempt}.md").read_text(encoding="utf-8")
        name = "lesson.md" if status == "shipped" else "lesson.DRAFT_needs_human_review.md"
        (out / name).write_text(final_text, encoding="utf-8")
        self._write_log(st, status, final_attempt)
        self.log(f"\nResult: {status.upper()} after {len(hist)} attempt(s). Output: {out / name}")
        return {"status": status, "final_lesson": final_text}

    def n_update_memory(self, st: State) -> dict:
        hist = st["history"]
        first = hist[0]
        details = {c["id"]: {"reason": c["reason"], "evidence": c["evidence"]} for c in first["checks"] if not c["passed"]}
        self.memory.record_run({
            "run_id": st["run_id"], "topic": st["topic"], "status": st["status"], "attempts": len(hist),
            "tampered": bool(st.get("tampered")), "provider": self.s.provider,
            "generator_model": self.s.generator_model, "evaluator_model": self.s.evaluator_model,
            "rubric_version": self.rubric.get("version"), "guidelines_version": self.memory.guidelines_version(),
            "first_attempt_failed": sorted(details), "first_attempt_details": details,
            "failed_by_attempt": [[c["id"] for c in h["checks"] if not c["passed"]] for h in hist],
        })
        if st.get("tampered"):
            self.log("Memory: this run had a deliberate error, so it is NOT used for learning.")
        else:
            self.log("Memory: run saved. Checking whether there is something to learn...")
            learned = maybe_evolve(self.memory, self.rubric, self.evo_llm, self.s.evolve_threshold, self.log)
            if not learned:
                self.log("  nothing new to learn yet.")
        return {}

    # ------------------------------------------------------------ rejection log
    def _write_log(self, st: State, status: str, final_attempt: int) -> None:
        out = Path(st["out_dir"])
        hist = st["history"]
        (out / "rejection_log.json").write_text(json.dumps({
            "run_id": st["run_id"], "topic": st["topic"], "status": status, "final_attempt": final_attempt,
            "attempts": hist}, indent=2, ensure_ascii=False), encoding="utf-8")
        md = [f"# Rejection log: {st['topic']}", "",
              f"- Run: `{st['run_id']}`", f"- Final status: **{status.replace('_', ' ').upper()}**",
              f"- Attempts used: {len(hist)} of {1 + st['max_retries']} allowed",
              f"- Rubric version: {self.rubric.get('version')} | Provider: {self.s.provider} "
              f"(writer: {self.s.generator_model}, judge: {self.s.evaluator_model})"]
        if st.get("tampered"):
            md.append(f"- NOTE: a deliberate error (`{st['tamper']}`) was injected into attempt 1 for the demo.")
        for h in hist:
            total = len(h["checks"])
            ok = total - h["n_failed"]
            verdict = "PASSED" if h["passed"] else "REJECTED"
            md += ["", f"## Attempt {h['attempt']}: {verdict} ({ok}/{total} checks passed)"]
            failed = [c for c in h["checks"] if not c["passed"]]
            if failed:
                md += ["", "| Failed check | Judged by | Why it failed | Evidence | Fix requested |", "|---|---|---|---|---|"]
                for c in failed:
                    cell = lambda s: (s or "-").replace("|", "/").replace("\n", " ")
                    note = "" if c.get("evidence_verified", True) or not c["evidence"] else " (quote NOT found in lesson)"
                    md.append(f"| `{c['id']}` | {c['kind']} | {cell(c['reason'])} | {cell(c['evidence'][:140])}{note} | {cell(c['fix'])} |")
                if "changes_on_retry" in h:
                    md += ["", f"**What changed on the retry** ({h.get('diff_lines', '?')} lines differ from this draft):"]
                    md += [f"- {c}" for c in h["changes_on_retry"]] or ["- (the writer did not describe its changes)"]
            else:
                md += ["", "All checks passed. This draft was shipped."]
        if status != "shipped":
            md += ["", "> The loop ran out of retries. The best attempt is saved as `lesson.DRAFT_needs_human_review.md`. "
                       "It was NOT approved. A human must review it."]
        (out / "rejection_log.md").write_text("\n".join(md) + "\n", encoding="utf-8")
