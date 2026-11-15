# Rejection log: Introduction to RAG (Retrieval-Augmented Generation)

- Run: `run_20261115_194915`
- Final status: **SHIPPED**
- Attempts used: 2 of 3 allowed
- Rubric version: 1 | Provider: mock (writer: mock, judge: mock)
- NOTE: a deliberate error (`subtle_fact`) was injected into attempt 1 for the demo.

## Attempt 1: REJECTED (0/11 checks passed)

| Failed check | Judged by | Why it failed | Evidence | Fix requested |
|---|---|---|---|---|
| `reading_level` | code | average sentence is 24.9 words (max 14); longest sentence has 46 words (max 25); reading grade is 13.9 (max 8.0) | First, documents are tokenized, chunked and embedded into a latent space, then at inference time the query embedding is compared against the | Keep most sentences under 15 words and none over 25. One idea per sentence. Use everyday words. |
| `structure` | code | Missing required section(s): What you will learn; What is <topic>?; How <topic> works; A full example; Quick recap | Overview / Why / Architecture | Use exactly the required H2 headings, in the required order. Do not skip the example or the recap. |
| `length` | code | Only 199 words (minimum 600). | - | Aim for about 800-1000 words. Cut repeated ideas if too long; add a worked step if too short. |
| `jargon_defined` | code | Not explained at first use: context window, embedding, hallucination, knowledge cutoff, latent space, vector, vector database. | Large language models hallucinate and have a knowledge cutoff, so RAG leverages dense vector embeddings stored in a vector database and util | Define each technical word in simple words the first time you use it, e.g. 'a chunk means a small piece of a document'. Or do not use the word. |
| `no_known_misconceptions` | code | False or unsupported claim. The truth: RAG does not retrain or fine-tune the LLM. | RAG works by retraining the model on those chunks every night so that the weights are updated, which guarantees 100% accurate answers. | Remove the false or unsupported claim. Use only facts from the ground truth. Do not add percentages or numbers that are not in it. |
| `plain_words` | code | Idioms or hard words found: deep dive, e.g., etc., game changer, leverages, myriad, under the hood. | Retrieval-Augmented Generation (RAG) is a game changer in modern AI because it combines a parametric large language model with a non-paramet | Replace idioms and fancy words with plain everyday words. Write 'for example' instead of 'e.g.'. |
| `accurate_grounded` | llm | A claim contradicts the ground truth. | RAG works by retraining the model on those chunks every night so that the weights are updated, which guarantees 100% accurate answers. | Rewrite the sentence so it matches the ground truth, or delete it. |
| `covers_key_points` | llm | Missing key points: prompt, out-of-date knowledge, private data, a limit of RAG. | - | Add the missing key points and explain each in 2-3 short sentences. |
| `teaches_by_example` | llm | There is no worked example that shows retrieve, augment and generate with sample text. | - | Add a concrete worked example with real sample text for each step. |
| `coherent_flow` | llm | The sections are missing or out of order, so the learner has to jump ahead. | - | Put the sections in the order what, why, how, example, recap. |
| `audience_fit` | llm | Talking-down words or hard wording make this hard for the learner. | Obviously this is simply the best approach, and it is easy once you know it. | Use simple words and remove talking-down words. |

**What changed on the retry** (123 lines differ from this draft):
- Rewrote every sentence to be short and use everyday words.
- Added the missing sections: A full example and Quick recap.
- Explained each technical word the first time it appears.
- Removed idioms and the false claims about retraining.

## Attempt 2: PASSED (11/11 checks passed)

All checks passed. This draft was shipped.
