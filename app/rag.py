"""Central RAG service for the EST Fquih Ben Salah chatbot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore


EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
DEFAULT_RETRIEVAL_K = 3


@dataclass(frozen=True)
class RAGResponse:
    """Answer returned by the RAG service."""

    answer: str
    sources: list[str]


class RAGService:
    """Reusable RAG pipeline shared by the FastAPI app and CLI chatbot."""

    def __init__(
        self,
        *,
        index_name: str,
        embedding_model: str = EMBEDDING_MODEL,
        llm_model: str = DEFAULT_LLM_MODEL,
        retrieval_k: int = DEFAULT_RETRIEVAL_K,
        temperature: float = 0.3,
    ) -> None:
        if not index_name:
            raise RuntimeError("Missing required environment variable: PINECONE_INDEX_NAME")

        self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model)
        self.vector_store = PineconeVectorStore(
            index_name=index_name,
            embedding=self.embeddings,
        )
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": retrieval_k},
        )
        self.llm = ChatGroq(
            model=llm_model,
            temperature=temperature,
            request_timeout=30,
        )
        self.prompt = ChatPromptTemplate.from_template(
            """Tu es l'assistant virtuel officiel de l'EST Fquih Ben Salah (EST FBS).
Ton rôle est d'aider les étudiants en répondant à leurs questions.
Utilise uniquement le contexte fourni ci-dessous pour répondre.
Si la réponse ne se trouve pas dans le contexte, dis poliment que tu ne sais pas et conseille de contacter l'administration.

Historique de conversation:
{history}

Contexte extrait des documents:
{context}

Question de l'étudiant:
{question}

Réponse:"""
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def ask(self, question: str, history: list[dict[str, Any]] | None = None) -> RAGResponse:
        """Answer a question using retrieved context and optional conversation history."""
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        docs = self.retriever.invoke(cleaned_question)
        context = self._format_docs(docs)
        formatted_history = self._format_history(history or [])
        answer = self.chain.invoke(
            {
                "history": formatted_history,
                "context": context,
                "question": cleaned_question,
            }
        )

        sources = sorted(
            {
                Path(doc.metadata.get("source", "Doc")).name
                for doc in docs
                if getattr(doc, "metadata", None) is not None
            }
        )
        return RAGResponse(answer=answer, sources=sources)

    @staticmethod
    def _format_docs(docs: list[Any]) -> str:
        """Convert retrieved documents into prompt context."""
        return "\n\n".join(doc.page_content for doc in docs)

    @staticmethod
    def _format_history(history: list[dict[str, Any]], max_turns: int = 6) -> str:
        """Convert Chainlit history into compact prompt text."""
        if not history:
            return "Aucun historique."

        turns = []
        for item in history[-max_turns:]:
            user_text = str(item.get("user", "")).strip()
            bot_text = str(item.get("bot", "")).strip()
            if user_text:
                turns.append(f"Etudiant: {user_text}")
            if bot_text:
                turns.append(f"Assistant: {bot_text}")

        return "\n".join(turns) if turns else "Aucun historique."


def create_rag_service() -> RAGService:
    """Create the RAG service from environment variables."""
    load_dotenv()
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        raise RuntimeError("Missing required environment variable: PINECONE_INDEX_NAME")

    return RAGService(
        index_name=index_name,
        embedding_model=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL),
        llm_model=os.getenv("GROQ_MODEL", DEFAULT_LLM_MODEL),
    )
