"""Command-line chatbot that reuses the shared RAG service."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.rag import create_rag_service  # noqa: E402


def lancer_chatbot() -> None:
    """Run the EST FBS chatbot in an interactive terminal session."""
    print("Starting EST FBS chatbot...")
    rag_service = create_rag_service()
    history: list[dict[str, str]] = []

    print("Chatbot ready. Type 'quit' to exit.\n")
    print("-" * 50)

    while True:
        question = input("Toi : ").strip()
        if question.lower() == "quit":
            print("Au revoir !")
            break
        if not question:
            continue

        print("Bot is reading the documents...")
        try:
            result = rag_service.ask(question, history)
        except Exception:
            print("Something went wrong, please try again.")
            continue
        history.append({"user": question, "bot": result.answer})
        history = history[-10:]

        print(f"\nEST FBS Bot : {result.answer}")
        if result.sources:
            print("\nSources consultees :")
            for source in result.sources:
                print(f"- {source}")
        print("-" * 50)


if __name__ == "__main__":
    lancer_chatbot()
