# Sample outputs

Both runs were produced with the **offline mock provider**, so they show the *shape* of the outputs (lesson, rejection log, attempts, evaluation JSON). They say nothing about how well a real model writes or judges.

- `mock_run_weak_first_draft/` — the mock writer's first draft is deliberately bad (11 of 11 checks fail). The log shows every reason, the fixes requested, and what changed on the retry.
- `mock_run_deliberate_error/` — a good draft with one planted false sentence (`--tamper subtle_fact`). Only the LLM-judge layer can catch it; the log shows it rejected on `accurate_grounded`, then fixed.

Open `rejection_log.md` in each run folder first.
