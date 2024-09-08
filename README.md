Simple RAG with Obsidian Notes
=============================

This project is an educational tool designed to demonstrate a basic Retrieval-Augmented Generator (RAG) system using Obsidian notes. The goal is to provide a simple and accessible example of how to integrate a knowledge base with a language model to generate human-like text.

What is RAG?
------------

Retrieval-Augmented Generator (RAG) is a type of language model that combines the strengths of retrieval-based and generation-based approaches. It retrieves relevant information from a knowledge base and uses this information to generate text.

How to Use
------------

1. Install Requirements: Install the required libraries by running `pip install -r requirements.txt`.

2. Set up Obsidian Notes: Create an Obsidian vault and add your notes. The project assumes that your notes are stored in a directory called `MainVault`.

3. Configure the Project: Update the `vd_update.py` file with your Obsidian vault path and other configuration settings.

4. Run the Project: Run the `vd_update.py` file to initialize the RAG system.

5. Query the System: Use the `query_engine` function to ask questions or provide prompts to the system. The system will retrieve relevant information from your Obsidian notes and generate a response.

Example Use Case
----------------

Query: "What is the main idea of the paper 'Language models are Unsupervised Multitask Learners - GPT-2'?"

Response: "The paper discusses how language models can be trained as unsupervised multitask learners, and how this approach can lead to state-of-the-art results on a variety of natural language processing tasks."

Note
----

This project is a simplified example of a RAG system and is intended for educational purposes only. The performance of the system may vary depending on the quality and quantity of the notes in your Obsidian vault.