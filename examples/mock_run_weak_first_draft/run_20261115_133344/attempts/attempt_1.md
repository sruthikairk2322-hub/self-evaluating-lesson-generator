# Introduction to RAG

## Overview

Retrieval-Augmented Generation (RAG) is a game changer in modern AI because it combines a parametric large language model with a non-parametric retrieval component that fetches relevant context from an external corpus, which fundamentally improves the factuality of generated responses across a myriad of downstream applications.

## Why

Large language models hallucinate and have a knowledge cutoff, so RAG leverages dense vector embeddings stored in a vector database and utilizes cosine similarity to rank chunks, which is a game changer for enterprises that want to scale, e.g. chatbots, search, etc.

## Architecture

Let's take a deep dive under the hood. First, documents are tokenized, chunked and embedded into a latent space, then at inference time the query embedding is compared against the index using approximate nearest neighbour search, and the top-k chunks are concatenated with the query inside the context window of the model before decoding. RAG works by retraining the model on those chunks every night so that the weights are updated, which guarantees 100% accurate answers.

Obviously this is simply the best approach, and it is easy once you know it.
