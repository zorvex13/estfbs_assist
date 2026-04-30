"""FastAPI entrypoint for the EST FBS RAG chatbot."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
WEB_API_DIR = Path(__file__).resolve().parent
if str(WEB_API_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_API_DIR))

from app.rag import RAGService, create_rag_service  # noqa: E402
from app.database import init_db, log_interaction  # noqa: E402


load_dotenv()

rag_service: RAGService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize database and RAG dependencies once at application startup."""
    global rag_service

    init_db()
    try:
        rag_service = create_rag_service()
        print("RAG service is ready.")
    except Exception as exc:
        rag_service = None
        raise RuntimeError(f"Failed to initialize RAG service: {exc}") from exc
    yield


app = FastAPI(title="Chatbot EST FBS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    """Incoming question payload from the frontend or development clients."""

    question: str | None = Field(default=None, min_length=1)
    text: str | None = Field(default=None, min_length=1)
    history: list[dict[str, Any]] = Field(default_factory=list)

    def normalized_text(self) -> str:
        """Return the supported question field with surrounding whitespace removed."""
        value = (self.question or self.text or "").strip()
        if not value:
            raise ValueError("Question cannot be empty.")
        return value


def _chunk_count() -> int | None:
    """Best-effort Pinecone vector count for the health response."""
    if rag_service is None:
        return None

    vector_store_index = getattr(rag_service.vector_store, "index", None)
    if vector_store_index is None:
        vector_store_index = getattr(rag_service.vector_store, "_index", None)
    if vector_store_index is None or not hasattr(vector_store_index, "describe_index_stats"):
        return None

    try:
        stats = vector_store_index.describe_index_stats()
    except Exception:
        return None

    if isinstance(stats, dict):
        total = stats.get("total_vector_count")
    else:
        total = getattr(stats, "total_vector_count", None)
    return int(total) if total is not None else None


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    """Serve the single-file chatbot frontend."""
    return FileResponse(SRC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, Any]:
    """Report basic API readiness for the frontend status indicator."""
    ready = rag_service is not None
    return {
        "status": "online" if ready else "offline",
        "ok": ready,
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "chunk_count": _chunk_count(),
    }


@app.post("/ask")
def poser_question(q: Question) -> dict[str, Any]:
    """Answer a student question and log the interaction."""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service is not initialized.")

    try:
        question = q.normalized_text()
        result = rag_service.ask(question, q.history)
        log_interaction(question, result.answer, result.sources)
        return {"answer": result.answer, "reponse": result.answer, "sources": result.sources}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"RAG request failed: {exc}")
        raise HTTPException(status_code=500, detail="AI service failed to answer.") from exc


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
