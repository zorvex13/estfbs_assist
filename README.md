# estfbs-assist

RAG-based chatbot backend for EST Fquih Ben Salah, built with FastAPI, LangChain, Groq, Gemini Embeddings, Pinecone, and Supabase.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![License](https://img.shields.io/badge/License-MIT-green)

## How It Works

```text
data/*.pdf, data/*.txt
        |
        v
scripts/load_vectors.py
        |
        v
Pinecone vector index
        |
        v
POST /ask
        |
        v
Groq + Llama 3.3 70B
        |
        v
Supabase logging
        |
        v
JSON response
```

## Prerequisites

- Groq console account at https://console.groq.com (free, no credit card)
- Google AI Studio API key for Gemini Embeddings
- Pinecone account with a free-tier index
- Supabase project with a PostgreSQL database
- Python 3.11+

## Tech Stack

- Python 3.11+
- FastAPI
- LangChain
- Groq (Llama 3.3 70B)
- Gemini Embeddings
- Pinecone
- Supabase PostgreSQL via SQLAlchemy

## Installation

```bash
git clone <repository-url>
cd est_fbs_chatbot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```bash
venv\Scripts\activate
```

## Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_ai_studio_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_pinecone_index_name_here
DATABASE_URL=your_supabase_postgres_connection_string_here
```

## Usage

1. Embed and upload school documents to Pinecone once:

```bash
python scripts/load_vectors.py
```

2. Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Reference

### POST `/ask`

Ask a question using the RAG pipeline.

Request:

```json
{
  "text": "What programs does EST FBS offer?",
  "history": [
    {
      "user": "Hello",
      "bot": "Hello, how can I help you?"
    }
  ]
}
```

Response:

```json
{
  "reponse": "EST FBS offers programs based on the available school documents.",
  "sources": [
    "presentation.txt"
  ]
}
```

## Project Structure

```text
app/
  main.py          FastAPI server and /ask endpoint
  rag.py           RAG pipeline using Pinecone, Groq, and Gemini Embeddings
  database.py      Supabase logging via SQLAlchemy
data/
  *.pdf / *.txt    School documents used as the knowledge base
scripts/
  load_vectors.py  One-time script to embed and upload documents to Pinecone
  chat.py          CLI chatbot for development and testing only
requirements.txt   Python dependencies
.env               Local environment variables, not committed
```
