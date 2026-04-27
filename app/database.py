"""Database helpers for storing chatbot interactions."""

import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

Base = declarative_base()
_engine: Any | None = None
_SessionLocal: sessionmaker | None = None


def _get_database_url() -> str:
    """Return DATABASE_URL with a clear error when it is missing."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Missing required environment variable: DATABASE_URL")
    return database_url


def get_engine() -> Any:
    """Create the SQLAlchemy engine only when the API actually starts."""
    global _engine

    if _engine is None:
        _engine = create_engine(_get_database_url(), pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker:
    """Return the configured SQLAlchemy session factory."""
    global _SessionLocal

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


class ChatLog(Base):
    """Stored chatbot question/answer interaction."""

    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Text, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    question = Column(Text)
    reponse = Column(Text)
    sources = Column(Text)


def init_db() -> None:
    """Crée la table sur Supabase si elle n'existe pas encore."""
    try:
        Base.metadata.create_all(bind=get_engine())
        print("Connexion à Supabase (Cloud) réussie.")
    except Exception as exc:
        raise RuntimeError(f"Erreur de connexion Cloud: {exc}") from exc


def log_interaction(question: str, reponse: str, sources: list[str] | str | None) -> None:
    """Enregistre l'interaction de l'étudiant directement dans le Cloud."""
    db = get_session_factory()()
    try:
        if sources and isinstance(sources, list):
            sources_str = ", ".join(sources)
        elif sources:
            sources_str = str(sources)
        else:
            sources_str = "Aucune source consultée"

        new_log = ChatLog(
            question=question,
            reponse=reponse,
            sources=sources_str,
        )

        db.add(new_log)
        db.commit()
        print(f"Log sauvegardé: {question[:30]}...")
    except Exception as exc:
        print(f"Erreur lors de l'enregistrement Cloud: {exc}")
        db.rollback()
    finally:
        db.close()
