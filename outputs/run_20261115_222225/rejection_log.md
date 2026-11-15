# Rejection log: Introduction to RAG (Retrieval-Augmented Generation)

- Run: `run_20261115_222225`
- Final status: **NEEDS HUMAN REVIEW**
- Attempts used: 3 of 3 allowed
- Rubric version: 1 | Provider: ollama (writer: llama3.2, judge: llama3.2)

## Attempt 1: REJECTED (3/11 checks passed)

| Failed check | Judged by | Why it failed | Evidence | Fix requested |
|---|---|---|---|---|
| `reading_level` | code | longest sentence has 29 words (max 25) | It is a technique where a large language model (LLM) is given relevant information, retrieved from an outside source at question time, and w | Keep most sentences under 15 words and none over 25. One idea per sentence. Use everyday words. |
| `structure` | code | Missing required section(s): What you will learn; What is <topic>?; Why do we need <topic>?; How <topic> works; A full example; Quick recap | - | Use exactly the required H2 headings, in the required order. Do not skip the example or the recap. |
| `length` | code | Only 472 words (minimum 600). | - | Aim for about 800-1000 words. Cut repeated ideas if too long; add a worked step if too short. |
| `accurate_grounded` | llm | The judge's answer could not be read (Expecting ',' delimiter: line 1 column 1351 (char 1350)), so it counts as a fail. | - | Rewrite the false sentence so it matches the ground truth, or delete it. |
| `covers_key_points` | llm | The judge's answer could not be read (Expecting ',' delimiter: line 1 column 1351 (char 1350)), so it counts as a fail. | - | Add the missing key point and explain it in 2-3 short sentences. |
| `teaches_by_example` | llm | The judge's answer could not be read (Expecting ',' delimiter: line 1 column 1351 (char 1350)), so it counts as a fail. | - | Add a concrete worked example with real sample text for every step, and one everyday analogy. |
| `coherent_flow` | llm | The judge's answer could not be read (Expecting ',' delimiter: line 1 column 1351 (char 1350)), so it counts as a fail. | - | Move or add explanations so every idea is introduced before it is used. Make the recap repeat only what was taught. |
| `audience_fit` | llm | The judge's answer could not be read (Expecting ',' delimiter: line 1 column 1351 (char 1350)), so it counts as a fail. | - | Simplify the explanation, remove talking-down words, and use a familiar example. |

**What changed on the retry** (32 lines differ from this draft):
- Added sentence limit to every sentence (max 25 words)
- Fixed structure and length
- Fixed accuracy and key point coverage
- Fixed teaching by example and flow
- Simplified explanation for non-native readers
- Added the example of RAG reducing hallucinations
- Added the list of words to know

## Attempt 2: REJECTED (3/11 checks passed)

| Failed check | Judged by | Why it failed | Evidence | Fix requested |
|---|---|---|---|---|
| `reading_level` | code | longest sentence has 29 words (max 25) | It is a technique where a large language model (LLM) is given relevant information, retrieved from an outside source at question time, and w | Keep most sentences under 15 words and none over 25. One idea per sentence. Use everyday words. |
| `structure` | code | Missing required section(s): What you will learn; What is <topic>?; Why do we need <topic>?; How <topic> works; A full example; Quick recap | - | Use exactly the required H2 headings, in the required order. Do not skip the example or the recap. |
| `length` | code | Only 595 words (minimum 600). | - | Aim for about 800-1000 words. Cut repeated ideas if too long; add a worked step if too short. |
| `accurate_grounded` | llm | The judge did not return a verdict for this check, so it counts as a fail. | - | Rewrite the false sentence so it matches the ground truth, or delete it. |
| `covers_key_points` | llm | The judge did not return a verdict for this check, so it counts as a fail. | - | Add the missing key point and explain it in 2-3 short sentences. |
| `teaches_by_example` | llm | The judge did not return a verdict for this check, so it counts as a fail. | - | Add a concrete worked example with real sample text for every step, and one everyday analogy. |
| `coherent_flow` | llm | The judge did not return a verdict for this check, so it counts as a fail. | - | Move or add explanations so every idea is introduced before it is used. Make the recap repeat only what was taught. |
| `audience_fit` | llm | The lesson uses technical terms such as 'vector database' and 'knowledge cutoff' without explaining them in simple words. | - | Explain technical terms in simple words |

**What changed on the retry** (42 lines differ from this draft):
- Added simple explanations for technical terms
- Added the missing key point about the limit of RAG
- Added a worked example with real sample text for every step
- Added an everyday analogy to help understand RAG

## Attempt 3: REJECTED (5/11 checks passed)

| Failed check | Judged by | Why it failed | Evidence | Fix requested |
|---|---|---|---|---|
| `reading_level` | code | longest sentence has 29 words (max 25) | It is a technique where a large language model (LLM) is given relevant information, retrieved from an outside source at question time, and w | Keep most sentences under 15 words and none over 25. One idea per sentence. Use everyday words. |
| `structure` | code | Missing required section(s): What you will learn; What is <topic>?; Why do we need <topic>?; How <topic> works; A full example; Quick recap | - | Use exactly the required H2 headings, in the required order. Do not skip the example or the recap. |
| `accurate_grounded` | llm | The claim that RAG reduces hallucinations but does not remove them completely contradicts the ground truth. | - | Clarify that RAG reduces hallucinations but does not remove them completely. |
| `covers_key_points` | llm | The lesson does not explain what each word in the name 'RAG' means. | - | Explain what each word in the name 'RAG' means. |
| `coherent_flow` | llm | The lesson jumps from explaining how RAG works to providing an example without explaining the steps in between. | - | Explain the steps in between how RAG works. |
| `audience_fit` | llm | The lesson uses technical terms such as 'LLM' and 'database' without explaining them in simple words. | - | Explain technical terms such as 'LLM' and 'database' in simple words. |

> The loop ran out of retries. The best attempt is saved as `lesson.DRAFT_needs_human_review.md`. It was NOT approved. A human must review it.
