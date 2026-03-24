# AAI2026
# Build a Simple Agentic AI Chatbot

## Overview
This project is a simple agentic AI customer service chatbot built with LangGraph and Google Gemini API. It simulates a customer service or sales assistant that can respond to user questions, provide support, recommend products, and maintain context across multiple turns.

## Features
- System prompt that defines the chatbot’s role as a customer service and sales assistant
- Three distinct agents:
  - Order Status Agent
  - Refund Policy Agent
  - Product Suggestion Agent
- LangGraph routing logic to send the user request to the correct agent
- LangGraph MemorySaver to maintain conversation state for at least 3 turns
- Google Gemini API integration
- Google Colab notebook for easy execution and demo

## Starter Repository Reference
This project was inspired by the starter examples in the repository:
https://github.com/myrah/build-ai-agents-and-chatbots-with-langgraph-2021112

I adapted the order chatbot, product Q&A, and multi-agent routing ideas into one chatbot and replaced the original Azure-based setup with Google Gemini API.

## Files
- `app.py` – main chatbot application
- `requirements.txt` – required Python packages
- `Agentic_AI_Chatbot_Gemini_Colab.ipynb` – Colab notebook version
- `README.md` – project explanation

## Setup
1. Open the Colab notebook or run locally.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
