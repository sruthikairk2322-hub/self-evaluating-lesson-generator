### RETRY
Your previous draft was REJECTED by the quality reviewer.

### What you will learn
This lesson introduces the concept of Retrieval-Augmented Generation (RAG), a technique used in artificial intelligence to generate answers from large language models.

### What is RAG?
RAG stands for Retrieval-Augmented Generation. It's a technique where a large language model (LLM) is given relevant information, retrieved from an outside source at question time, and writes its answer using that information.

### Why do we need RAG?
We need RAG to help large language models improve their performance and accuracy. There are three main problems RAG helps with:

*   The knowledge of the model can be out of date.
*   The model has no access to private or company-specific information.
*   The model can give wrong answers.

RAG helps address these problems by retrieving relevant information from an outside source and using that information to generate an accurate answer.

### How RAG works
Here's an overview of how RAG works:

*   Before any question, you collect documents, split them into chunks, turn each chunk into an embedding, and store chunks and embeddings in a vector database.
*   At question time, you turn the question into an embedding and find the chunks closest in meaning. You keep only the best few, not the whole library.
*   Next, you build a prompt that contains the user's question, the retrieved chunks, and an instruction to answer only from the text given.
*   Finally, you give the LLM this prompt, and it writes the answer, grounded in the retrieved chunks. Good systems also show the sources.

### A full example
Let's consider a question: "What are the benefits of using a large language model?"

*   Before any question, you have a document with the following text: "Large language models have several benefits, including improved accuracy, increased efficiency, and better ability to understand context."
*   At question time, you turn the question into an embedding and find the chunks closest in meaning. Let's say the top-k chunks are: "Improved accuracy", "Increased efficiency", and "Better ability to understand context".
*   Next, you build a prompt that contains the question, the retrieved chunks, and an instruction to answer only from the text given: "Answer only from the text given: What are the benefits of using a large language model?"
*   Finally, you give the LLM this prompt, and it writes the answer: "The benefits of using a large language model include improved accuracy, increased efficiency, and better ability to understand context."

### Quick recap
In summary, RAG is a technique used in artificial intelligence to generate answers from large language models. It helps address problems such as outdated knowledge, limited access to private information, and wrong answers by retrieving relevant information from an outside source and using that information to generate an accurate answer.

### Check yourself
Can you think of a time when you used a large language model to get an answer?

### Words to know
Here's a list of key terms related to RAG:

*   LLM: Large Language Model
*   Embedding: A list of numbers that captures the meaning of a chunk
*   Vector database: A store that holds chunks and their corresponding embeddings
*   Prompt: A question or instruction that guides the LLM's answer

###
