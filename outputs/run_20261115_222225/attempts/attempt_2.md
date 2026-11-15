### RETRY (attempt 3)
#### What You Will Learn
This lesson introduces Retrieval-Augmented Generation (RAG), a technique to improve the performance of large language models. By the end of this lesson, you will understand the basics of RAG and how it works.

#### What Is RAG?
RAG stands for Retrieval-Augmented Generation. It is a technique where a large language model (LLM) is given relevant information, retrieved from an outside source at question time, and writes its answer using that information. The name RAG was introduced in a 2020 research paper led by Patrick Lewis at Facebook AI Research (now Meta).

#### Why Do We Need RAG?
There are three problems that RAG helps with:

1. **Out-of-date knowledge**: The knowledge cutoff of an LLM is fixed after training, which means it can become outdated quickly. RAG updates the documents instead of retraining the LLM.
2. **Limited access to information**: An LLM has no access to private or company-specific information. RAG retrieves relevant information from outside sources.
3. **Hallucination**: An LLM can give a confident answer that is wrong or made up. RAG reduces hallucinations but does not remove them completely.

#### How RAG Works
Here's a step-by-step explanation of how RAG works:

1. **Before any question (indexing)**: Collect documents and split them into chunks (small pieces, often a few sentences). Turn each chunk into an embedding (a list of numbers that captures its meaning). Store chunks and embeddings in a vector database (or similar index).

2. **At question time**:
	* **Step 1: Retrieve**: Turn the question into an embedding and find the chunks closest in meaning. Keep only the best few (top-k), not the whole library.
	* **Step 2: Augment**: Build a prompt that contains the user's question, the retrieved chunks, and an instruction (for example, answer only from the text given).
	* **Step 3: Generate**: The LLM reads the prompt and writes the answer, grounded in the retrieved chunks. Good systems also show the sources.

3. **A Full Example**
Let's consider an example where a user asks, "What is the capital of France?"

1. **Before any question**: We collect documents and split them into chunks. We turn each chunk into an embedding and store them in a vector database.

2. **At question time**:
	* **Step 1: Retrieve**: We turn the question into an embedding and find the chunks closest in meaning. Let's say we find two chunks: "France is a country in Europe" and "The capital of France is Paris". We keep the top two chunks.
	* **Step 2: Augment**: We build a prompt that contains the user's question, the retrieved chunks, and an instruction. The prompt might look like this: "What is the capital of France? Answer only from the text given."
	* **Step 3: Generate**: The LLM reads the prompt and writes the answer, grounded in the retrieved chunks. The answer might be: "The capital of France is Paris."

4. **How RAG Reduces Hallucinations**
RAG reduces hallucinations by retrieving relevant information from outside sources. However, if the retrieved chunks are wrong or the documents are outdated, the answer can still be incorrect.

#### Why RAG Is Useful
RAG is useful for company or college help bots, customer support, question answering over a set of documents, and study assistants.

#### Quick Recap
In summary, RAG is a technique that improves the performance of large language models by retrieving relevant information from outside sources and writing answers using that information. It helps with out-of-date knowledge, limited access to information, and hallucination.

#### What RAG Cannot Do
RAG does not remove hallucinations completely. It also requires a large amount of training data and a vector database to store the chunks and embeddings.

#### Check Yourself
Before answering any questions, make sure you understand the basics of RAG and how it works.

#### Words to Know
- **LLM**: Large Language Model
- **Vector Database**: A database that stores chunks and embeddings
- **Knowledge Cutoff**: The date after which an LLM's training data stops being updated
