# Introduction to RAG: Teaching an AI to Look Things Up

## What you will learn

After this lesson, you will be able to:

- Explain what RAG is in your own words.
- Say why people use it.
- Describe how it works, using a real example.

You do not need any AI knowledge to start. We will explain every new word.

## What is RAG?

RAG stands for **Retrieval-Augmented Generation**. The name sounds difficult, but we will take it step by step. Let us look at the three words one by one.

- **Retrieval** means finding information.
- **Augmented** means made better by adding something.
- **Generation** means writing a new answer.

So, RAG means this: first find the right information, then add it to the question, then write the answer.

Here is a way to remember it. Think about two kinds of exams. In a closed-book exam, you can use only what you remember. In an open-book exam, you can look inside your textbook before you write. RAG gives an AI the open-book exam.

Which AI do we mean? We mean a **large language model** (LLM). An LLM is a computer program that reads and writes text. Tools like ChatGPT and Claude are built on LLMs.

Researchers at Facebook AI (now Meta) gave RAG its name in a 2020 research paper. Today, many companies use the idea.

## Why do we need RAG?

An LLM learns by reading a huge amount of text. This is called **training**. When training ends, the LLM stops learning. This causes three problems.

1. **It can be out of date.** The LLM knows only what it read before training stopped. The date when its learning stopped is called the **knowledge cutoff**. The LLM does not know news after that date.
2. **It does not know your private information.** It never read your college notices, your company rules, or your personal files.
3. **It can make things up.** Sometimes an LLM does not know the answer, but it still sounds sure. The answer may be wrong. This is called a **hallucination**.

We could teach the LLM again every time the information changes. But that is slow and costly. RAG is a better way. We give the LLM the right text at the moment it needs to answer. Then it can answer from that text instead of guessing.

## How RAG works

RAG has two parts. First, we prepare a library. Then, we answer questions using that library.

### Part 1: Prepare the library

This is done once, before any question.

1. Collect your documents, such as PDF files, web pages, and notices.
2. Cut each document into small pieces called **chunks**. A chunk is usually a few sentences.
3. Turn each chunk into a list of numbers that shows its meaning. This list is called an **embedding**. Chunks with similar meanings get similar numbers.
4. Save the chunks and their embeddings in a special database called a **vector database**.

Because of embeddings, the computer can find text by meaning, not only by exact words. For example, a question about the "last date" can match a chunk that says "pay by 20 March".

### Part 2: Answer a question

There are three steps.

Question → Retrieve → Augment → Generate → Answer

**Step 1: Retrieve.** The system turns the user's question into an embedding. Then it searches the database for the chunks with the closest meaning. It picks only the best few, for example the top 3.

**Step 2: Augment.** The system builds a new message for the LLM. This message is called a **prompt**. The prompt holds the user's question, the chunks we found, and an instruction such as "Answer using only the text below."

**Step 3: Generate.** The LLM reads the prompt and writes the answer from those chunks. Good apps also show the source, so the user can check the answer.

Notice what did not change: the LLM itself. RAG does not change the LLM. It gives the LLM the right notes at the right time.

## A full example

Imagine a chatbot for an imaginary school called Sunrise College. A student asks:

> "What is the last date to pay the exam fee?"

**Without RAG.** The LLM never read the notices of Sunrise College. It may guess a date. A wrong guess is a hallucination.

**With RAG.**

1. **Retrieve.** The system searches the college notices. It finds this chunk: "Exam fee must be paid by 20 March. After that date, a late fee of ₹500 applies."
2. **Augment.** The system sends the LLM a prompt: "Answer using only the notice below. Notice: Exam fee must be paid by 20 March. After that date, a late fee of ₹500 applies. Question: What is the last date to pay the exam fee?"
3. **Generate.** The LLM answers: "The last date to pay the exam fee is 20 March. After that, you must pay a late fee of ₹500."

Now suppose the college changes the date. Nobody needs to teach the LLM again. The college only updates the notice. The next answer will use the new notice.

## What RAG cannot do

RAG is useful, but it is not perfect.

- If the search finds the wrong chunk, the answer can be wrong.
- If the documents are old or wrong, the answer will be old or wrong too.
- The LLM can still make mistakes. RAG makes hallucinations less likely, but it does not remove them completely.

So, good RAG apps show their sources, and people check important answers.

## Quick recap

- RAG means Retrieval-Augmented Generation: find information, add it to the prompt, then write the answer.
- We need it because an LLM can be out of date, can miss private information, and can hallucinate.
- First we prepare a library of chunks. Then, for each question, we retrieve, augment, and generate.
- RAG does not retrain the LLM. It gives the LLM the right notes at question time.

## Check yourself

1. What do the three words in the name RAG mean?
2. Name one problem of LLMs that RAG helps with.
3. In the college example, which step finds the notice?

**Answers**

1. Retrieval means finding information. Augmented means made better by adding something. Generation means writing a new answer.
2. Any one of these: the LLM can be out of date, it does not know private information, or it can hallucinate.
3. Step 1, Retrieve.

## Words to know

- **LLM (large language model):** A computer program that reads and writes text.
- **Training:** The time when an LLM learns by reading a lot of text.
- **Knowledge cutoff:** The date when an LLM's learning stopped.
- **Hallucination:** A confident answer that is wrong or made up.
- **Chunk:** A small piece of a document.
- **Embedding:** A list of numbers that shows the meaning of a text.
- **Vector database:** A database that stores embeddings and finds the ones closest in meaning.
- **Prompt:** The message we send to an LLM.
