"""Load local school documents into Pinecone using the project embedding model."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone


EMBEDDING_MODEL = "models/gemini-embedding-001"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"


def require_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def store_hybrid_data() -> None:
    """Split raw PDF/TXT files, embed them, and upsert chunks into Pinecone."""
    load_dotenv()

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data folder not found: {RAW_DATA_PATH}")

    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    print(f"Loading documents from {RAW_DATA_PATH}")
    for file_path in sorted(RAW_DATA_PATH.iterdir()):
        if file_path.suffix.lower() == ".pdf":
            print(f"Reading PDF: {file_path.name}")
            docs = PyPDFLoader(str(file_path)).load()
            all_chunks.extend(text_splitter.split_documents(docs))
        elif file_path.suffix.lower() == ".txt":
            print(f"Reading TXT: {file_path.name}")
            docs = TextLoader(str(file_path), encoding="utf-8").load()
            all_chunks.extend(text_splitter.split_documents(docs))

    if not all_chunks:
        raise RuntimeError(f"No PDF or TXT chunks found in {RAW_DATA_PATH}")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    pinecone = Pinecone(api_key=require_env("PINECONE_API_KEY"))
    index = pinecone.Index(require_env("PINECONE_INDEX_NAME"))

    print(f"Vectorizing {len(all_chunks)} chunks with {EMBEDDING_MODEL}...")
    for i, chunk in enumerate(all_chunks):
        vector = embeddings.embed_query(chunk.page_content)
        metadata = {
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", "Unknown"),
        }
        index.upsert(vectors=[(f"doc_{i}", vector, metadata)])

    print("All documents were uploaded to Pinecone.")


if __name__ == "__main__":
    store_hybrid_data()
