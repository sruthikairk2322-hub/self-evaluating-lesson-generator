# Self-Evaluating Lesson Generator

An agentic system that writes a beginner lesson, **judges its own work against a hard pass/fail rubric**, and **regenerates until the lesson clears the bar** (or stops and asks a human). It also keeps a memory and learns from its own repeated mistakes.

Topic for the submission: **Introduction to RAG (Retrieval-Augmented Generation)**.
Target learner: a 12th-grade graduate from India, no technical background, limited English vocabulary.

```
topic ──► GENERATE ──► EVALUATE ──pass──► SHIP  (lesson.md + rejection_log.md)
              ▲            │
              │          fail (max 2 retries)
              └─ REFLECT ◄─┘            out of retries ──► flagged "needs human review", never shipped
                 (reasons + quotes + fixes go back to the writer)

        MEMORY: failures and human feedback ──► learned guidelines ──► next writer prompt
```

Read **[DESIGN.md](DESIGN.md)** for the reasoning behind the structure, the evaluator and the trade-offs.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # then put ONE API key in .env
pytest -q                                               # 30 tests, no API key needed
```

`.env` (see `.env.example`): choose `anthropic` or `openai`. The judge can use a **different, stronger model** than the writer (`EVALUATOR_MODEL`), which reduces self-preference bias. With no key, the code falls back to an **offline mock** that tests the plumbing only. It says so loudly and is not evidence of real quality.

## Run

```bash
python run.py                          # full loop for "Introduction to RAG"
python run.py --tamper subtle_fact     # DEMO: plant a deliberate error and watch the evaluator catch it
python run.py --max-retries 1          # 1 or 2 (hard cap), loop always terminates
```

Deliberate errors (`--tamper`): `subtle_fact` (only the LLM judge can catch it), `wrong_origin`, `misconception`, `jargon`, `no_example`. Tampered runs are marked synthetic and are **never learned from**.

Each run writes `outputs/run_<timestamp>/`:

| File | What it is |
|---|---|
| `lesson.md` | the passing lesson (only exists if every check passed) |
| `rejection_log.md` / `.json` | per attempt: what failed, why, evidence quoted from the lesson, the fix requested, and **what changed on the retry** |
| `attempts/attempt_N.md`, `evaluation_N.json` | every draft and its full verdicts |
| `lesson.DRAFT_needs_human_review.md` | only if retries ran out: the best attempt, **not approved** |

See `examples/` for sample output (generated with the offline mock, so it shows the *format*, not model quality).

### Memory and self-evolution

```bash
python run.py feedback "Use a food example instead of an exam example" --check audience_fit
python run.py evolve        # turns pending human feedback + repeated failures into guidelines
python run.py memory        # shows what has been learned
```

`memory/guidelines.json` is injected into the next writer prompt. Failing the same check on the first attempt in several real runs (`EVOLVE_THRESHOLD`, default 2) also creates a guideline automatically. The rubric is **never edited by the system**; it can only write proposals to `memory/rubric_proposals.md` for a human.

## The rubric (11 hard pass/fail checks)

| Dimension in the brief | Check | Judged by |
|---|---|---|
| beginner-friendly language | `reading_level`, `plain_words` | code |
| clear, no unexplained jargon | `jargon_defined` (+ `audience_fit`) | code (+ LLM) |
| coherent teaching flow | `structure`, `coherent_flow` | code, LLM |
| covers the key points | `covers_key_points`, `length` | LLM, code |
| accurate & grounded | `accurate_grounded`, `no_known_misconceptions` | LLM (vs. a fact sheet), code |
| teaches by example | `teaches_by_example` | LLM |

The lesson ships only if **all 11** pass. Details and thresholds: `rubric.yaml`. Ground truth the judge uses: `knowledge/rag_facts.yaml`.

## Repo layout

```
run.py                  CLI
rubric.yaml             the quality bar (human-owned)
knowledge/rag_facts.yaml  ground truth for accuracy checks (human-reviewed)
prompts/                writer, judge and guideline-writer prompts
lesson_agent/
  graph.py              LangGraph state machine (the loop) + rejection log
  generator.py          writer prompt building, retry feedback, change-log parsing
  evaluator.py          code checks + LLM judge, fails closed
  deterministic.py      reading level, structure, jargon, misconceptions, plain words
  memory.py, evolve.py  persistent memory and the self-evolving step
  tamper.py             deliberate error injection for the demo
  llm.py, mock.py       Anthropic / OpenAI adapters, offline mock
fixtures/               mock writer outputs; reference_lesson.md
tests/                  30 tests (loop, termination, fail-closed judge, memory, adapters)
examples/               sample outputs (mock)
lesson_reference.md     a hand-written reference lesson (see note below)
```

## Using another topic

```bash
python run.py --topic "Introduction to Vector Databases" --facts knowledge/vector_db_facts.yaml
```

Copy `knowledge/rag_facts.yaml` and write a short, **human-reviewed** fact sheet (facts, common mistakes, jargon list, regex tripwires for known false claims). The evaluator can only check accuracy against something. The `required_sections` in `rubric.yaml` use generic labels and work for any topic.

## Note on `lesson_reference.md`

This is a lesson written by hand and checked by the six code checks; it is also what the offline mock returns as its "good" draft. For the submission, **generate the lesson with a real model** (`python run.py`) and use `outputs/<run>/lesson.md` and its `rejection_log.md`.
