# Rejection log: Introduction to RAG (Retrieval-Augmented Generation)

- Run: `run_20261115_133343`
- Final status: **SHIPPED**
- Attempts used: 2 of 3 allowed
- Rubric version: 1 | Provider: mock (writer: mock, judge: mock)
- NOTE: a deliberate error (`subtle_fact`) was injected into attempt 1 for the demo.

## Attempt 1: REJECTED (10/11 checks passed)

| Failed check | Judged by | Why it failed | Evidence | Fix requested |
|---|---|---|---|---|
| `accurate_grounded` | llm | A claim contradicts the ground truth. | In the Retrieve step, the LLM looks for the answer inside its own memory, so no database or documents are needed. | Rewrite the sentence so it matches the ground truth, or delete it. |

**What changed on the retry** (2 lines differ from this draft):
- Rewrote to fix the failed checks.

## Attempt 2: PASSED (11/11 checks passed)

All checks passed. This draft was shipped.
