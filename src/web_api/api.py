"""FastAPI entrypoint for the EST FBS RAG chatbot."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
WEB_API_DIR = Path(__file__).resolve().parent
if str(WEB_API_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_API_DIR))

from rag_chain import RAGService, create_rag_service  # noqa: E402
from database import init_db, log_interaction  # noqa: E402


load_dotenv()

app = FastAPI(title="Chatbot EST FBS")
rag_service: RAGService | None = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    """Incoming question payload from Chainlit."""

    text: str = Field(..., min_length=1)
    history: list[dict[str, Any]] = Field(default_factory=list)


@app.on_event("startup")
def startup() -> None:
    """Initialize database and RAG dependencies once at application startup."""
    global rag_service

    init_db()
    try:
        rag_service = create_rag_service()
        print("RAG service is ready.")
    except Exception as exc:
        rag_service = None
        raise RuntimeError(f"Failed to initialize RAG service: {exc}") from exc


@app.post("/ask")
def poser_question(q: Question) -> dict[str, Any]:
    """Answer a student question and log the interaction."""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service is not initialized.")

    try:
        result = rag_service.ask(q.text, q.history)
        log_interaction(q.text, result.answer, result.sources)
        return {"reponse": result.answer, "sources": result.sources}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"RAG request failed: {exc}")
        raise HTTPException(status_code=500, detail="AI service failed to answer.") from exc


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
