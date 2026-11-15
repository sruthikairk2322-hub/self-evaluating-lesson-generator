
#!/usr/bin/env python3

"""
Command line for the self-evaluating lesson generator.

Examples:

python run.py
python run.py run --provider ollama
python run.py run --provider ollama --tamper subtle_fact
python run.py feedback "Use shorter sentences" --check reading_level
python run.py evolve
python run.py memory
"""

from __future__ import annotations

import argparse
import json
import sys

from lesson_agent.config import load_settings
from lesson_agent.evolve import maybe_evolve
from lesson_agent.graph import Pipeline
from lesson_agent.llm import get_llm
from lesson_agent.memory import Memory
from lesson_agent.rubric import load_facts, load_rubric
from lesson_agent.tamper import TAMPERS


def main(argv: list[str] | None = None) -> int:

    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    p.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "feedback", "evolve", "memory"]
    )

    p.add_argument(
        "text",
        nargs="?",
        help="Feedback text"
    )

    p.add_argument(
        "--topic",
        default="Introduction to RAG (Retrieval-Augmented Generation)"
    )

    p.add_argument(
        "--facts",
        help="Path to the topic's ground-truth YAML"
    )

    p.add_argument(
        "--provider",
        choices=["anthropic", "openai", "ollama", "mock"],
        help="LLM provider"
    )

    p.add_argument(
        "--tamper",
        choices=sorted(TAMPERS),
        help="Inject a deliberate error into attempt 1"
    )

    p.add_argument(
        "--max-retries",
        type=int,
        help="1 or 2 (default 2)"
    )

    p.add_argument(
        "--check",
        help="Rubric check ID"
    )

    p.add_argument(
        "--memory-dir"
    )

    p.add_argument(
        "--out"
    )

    a = p.parse_args(argv)

    settings = load_settings(
        provider=a.provider,
        memory_dir=a.memory_dir,
        output_dir=a.out,
        max_retries=a.max_retries
    )

    rubric = load_rubric()
    memory = Memory(settings.memory_dir)

    # Save human feedback
    if a.command == "feedback":

        if not a.text:
            p.error("Please provide feedback text.")

        if a.check and a.check not in {
            c["id"] for c in rubric["checks"]
        }:
            p.error(f"Unknown check: {a.check}")

        memory.add_feedback(a.text, a.check)

        print("Feedback saved.")
        print("Run python run.py evolve to learn from feedback.")

        return 0

    # Evolve memory
    if a.command == "evolve":

        learned = maybe_evolve(
            memory,
            rubric,
            get_llm(settings, "evolver"),
            settings.evolve_threshold
        )

        print(
            "Learned: " + ", ".join(learned)
            if learned
            else "Nothing new to learn."
        )

        return 0

    # Display memory
    if a.command == "memory":

        doc = {
            "guidelines_version": memory.guidelines_version(),
            "guidelines": memory.active_guidelines(),
            "real_runs": len([
                r for r in memory.runs()
                if not r.get("tampered")
            ]),
            "synthetic_runs": len([
                r for r in memory.runs()
                if r.get("tampered")
            ]),
            "pending_feedback": len(
                memory.pending_feedback()
            )
        }

        print(json.dumps(
            doc,
            indent=2,
            ensure_ascii=False
        ))

        return 0

    if settings.provider == "mock":
        print(
            "NOTE: MOCK provider is active. "
            "This tests the workflow, not real AI quality."
        )

    if settings.provider == "ollama":
        print("Using local Ollama model.")
        print(f"Generator model: {settings.generator_model}")
        print(f"Evaluator model: {settings.evaluator_model}")

    facts = load_facts(a.facts)

    pipeline = Pipeline(
        settings,
        rubric=rubric,
        facts=facts
    )

    state = pipeline.run(
        a.topic,
        tamper=a.tamper
    )

    return 0 if state["status"] == "shipped" else 2


if __name__ == "__main__":
    sys.exit(main())
