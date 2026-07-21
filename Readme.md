# 🚀 LinkedIn AI Agent

An Agentic AI application that generates, reviews, and publishes LinkedIn posts using **LangGraph**, FastAPI, Streamlit, and the LinkedIn API.

## ✨ Features

- 🤖 AI-powered LinkedIn post generation
- 👨‍💻 Human-in-the-Loop review with LangGraph interrupts
- 🔄 Rewrite posts based on reviewer feedback
- 🚀 Publish approved posts directly to LinkedIn
- 💾 Persistent workflow state using MemorySaver
- 🌐 FastAPI backend with Streamlit frontend

## 🛠️ Tech Stack

- Python
- LangGraph
- LangChain
- Mistral AI
- FastAPI
- Streamlit
- LinkedIn REST API

## 📂 Project Structure

```
├── agent_graph.py
├── Backend.py
├── frontend.py
├── .env
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Add your API keys in `.env`

```env
MISTRAL_API_KEY=your_api_key
LINKEDIN_ACCESS_TOKEN=your_access_token
```

## 🔄 Workflow

```
Generate Draft
      ↓
Human Review
      ↓
Rewrite (if needed)
      ↓
Approve
      ↓
Publish to LinkedIn
```


Developed as an Agentic AI project to demonstrate workflow automation, Human-in-the-Loop AI, and LinkedIn content publishing.
