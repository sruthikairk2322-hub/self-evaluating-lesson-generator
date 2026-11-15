# Loom plan (15-20 min, face visible)

Record with your camera on for the intro, the architecture walk and the wrap-up. Share your screen for the demos. Do a real run first (see "Before recording").

## Before recording (about 15 min)
1. `pip install -r requirements.txt`, copy `.env.example` to `.env`, add your key. Run `pytest -q`: it should say 30 passed.
2. Do one real run: `python run.py`. Open `outputs/<run>/lesson.md` and `rejection_log.md`. Paste the lesson into a Google Doc for the submission form.
3. Delete or move `memory/` and `outputs/` contents if you want the video to start from a clean state.
4. Have these open in tabs: `README.md`, `DESIGN.md` (the diagram), `rubric.yaml`, `knowledge/rag_facts.yaml`, `lesson_agent/graph.py`, a terminal.

## Timeline

| Time | What you show | What you say |
|---|---|---|
| 0:00-1:30 | Face on camera | Who you are. The task in one sentence: "an agent that writes a lesson, judges it against a hard rubric, and regenerates until it is good enough to ship, or stops and asks a human." Who the learner is. |
| 1:30-5:00 | `DESIGN.md` diagram, then `graph.py` | Walk the loop: generate → evaluate → pass/retry/stop. Point out that the retry/stop decision is plain Python, not an LLM, so it always ends. Name the 4 parts: writer, evaluator, rubric, memory. |
| 5:00-8:00 | `rubric.yaml` and `rag_facts.yaml` | 11 hard pass/fail checks. 6 by code, 5 by an LLM judge. Why two layers. Why the judge gets a fact sheet to check "accurate and grounded". The judge fails closed. |
| 8:00-11:30 | Terminal: `python run.py` end to end | Narrate the console: attempt 1, the checks, any failure and its quoted evidence, the retry, the pass. Then open `lesson.md` and `rejection_log.md`. |
| 11:30-14:30 | Terminal: `python run.py --tamper subtle_fact` | "I plant one false sentence that no regex can catch." Show the evaluator rejecting `accurate_grounded` with the quoted sentence. Show the retry fixing it and the log's "what changed". Optionally run `--tamper jargon` to show the code layer catching things too. |
| 14:30-17:00 | Terminal: `python run.py feedback "..." --check audience_fit`, `python run.py evolve`, `python run.py memory` | Show `guidelines.json` growing. Run again: "Memory: 1 learned guideline(s) will be given to the writer." Explain: guidelines can evolve, the rubric cannot (humans own the bar); tampered runs are not learned from. |
| 17:00-19:00 | Face on camera, `DESIGN.md` section 6-9 | Trade-offs you made. Honest limits: the evaluator is only as good as the fact sheet; thresholds tuned on little data. What you would build next: judge calibration with human-labelled lessons, teach-back test. |
| 19:00-19:30 | Face on camera | One-line recap and thanks. |

## Tips
- Say the **why** for each choice, not only the what. That is what the brief asks for.
- If a real run passes on attempt 1, that is fine: the `--tamper` demo is your proof that the evaluator works. Also show `examples/mock_run_weak_first_draft/rejection_log.md` and say clearly that it is from the offline mock.
- Do not hide a failure. If the judge is too strict or too lenient in your real run, say so and show how you would tune it. That shows ownership.
