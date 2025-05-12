# Setup

This repository accompanies the [Build a Neo4j-backed Chatbot using Python course](https://graphacademy.neo4j.com/courses/llm-chatbot-python/) on [GraphAcademy](https://graphacademy.neo4j.com), modified to use Google's Generative AI (Gemini 2.0 Flash) instead of OpenAI.

When the devcontainer is created, such as in a GitHub codespace, all the required software and packages will be installed.

## Google Generative AI Setup

To use this project, you'll need to:

1. Create a Google Cloud account if you don't have one
2. Enable the Generative AI API
3. Create an API key
4. Create a `.streamlit/secrets.toml` file based on the example template and add your API key

Follow the [Setup Instructions in GraphAcademy](https://graphacademy.neo4j.com/courses/llm-chatbot-python/1-project-setup/2-setup/) for the Neo4j setup.

To start the chatbot, run:

```bash
streamlit run bot.py
``` 