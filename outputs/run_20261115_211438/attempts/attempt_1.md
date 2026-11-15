### What you will learn
This lesson introduces the concept of Retrieval-Augmented Generation (RAG), a technique used in artificial intelligence to generate answers from large language models.

### What is RAG?
RAG stands for Retrieval-Augmented Generation. It's a technique where a large language model (LLM) is given relevant information, retrieved from an outside source at question time, and writes its answer using that information.

### Why do we need RAG?
We need RAG to help large language models improve their performance and accuracy. Three main problems RAG helps with:

*   Knowledge can be out of date, which means the model's knowledge may not be up-to-date.
*   The model has no access to private or company-specific information, which can limit its ability to provide accurate answers.
*   The model can hallucinate, meaning it gives a confident answer that is wrong or made up.

RAG helps address these problems by retrieving relevant information from an outside source and using that information to generate an accurate answer.

### How RAG works
Here's an overview of how RAG works:

*   **Before any question:** Collect documents, split them into chunks (small pieces, often a few sentences), turn each chunk into an embedding (a list of numbers that captures its meaning), and store chunks and embeddings in a vector database (or similar index).
*   **At question time:** Step 1 **Retrieve**: Turn the question into an embedding and find the chunks closest in meaning. Keep only the best few (top-k), not the whole library.
*   Step 2 **Augment**: Build a prompt that contains the user's question, the retrieved chunks, and an instruction (for example, answer only from the text given).
*   Step 3 **Generate**: The LLM reads the prompt and writes the answer, grounded in the retrieved chunks. Good systems also show the sources.

### A full example
Let's consider a question: "What are the benefits of using a large language model?"

*   **Before any question:** We have a document with the following text: "Large language models have several benefits, including improved accuracy, increased efficiency, and better ability to understand context."
*   **At question time:** Step 1 **Retrieve**: Turn the question into an embedding and find the chunks closest in meaning. Let's say the top-k chunks are: "Improved accuracy", "Increased efficiency", and "Better ability to understand context".
*   Step 2 **Augment**: Build a prompt that contains the question, the retrieved chunks, and an instruction: "Answer only from the text given."
*   Step 3 **Generate**: The LLM reads the prompt and writes the answer: "The benefits of using a large language model include improved accuracy, increased efficiency, and better ability to understand context."

### Quick recap
In summary, RAG is a technique used in artificial intelligence to generate answers from large language models. It helps address problems such as out-of-date knowledge, limited access to private information, and hallucinations by retrieving relevant information from an outside source and using that information to generate an accurate answer.

###
