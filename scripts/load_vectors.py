"""Load local school documents into Pinecone using the project embedding model."""

import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone


EMBEDDING_MODEL = "models/gemini-embedding-001"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data"


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
    chunk_texts = [chunk.page_content for chunk in all_chunks]
    vectors = embeddings.embed_documents(chunk_texts)
    records = []
    for chunk, vector in zip(all_chunks, vectors):
        metadata = {
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", "Unknown"),
        }
        records.append(
            (hashlib.md5(chunk.page_content.encode()).hexdigest(), vector, metadata)
        )

    uploaded = 0
    for start in range(0, len(records), 100):
        batch = records[start : start + 100]
        index.upsert(vectors=batch)
        previous_uploaded = uploaded
        uploaded += len(batch)
        for progress in range(
            ((previous_uploaded // 50) + 1) * 50,
            uploaded + 1,
            50,
        ):
            print(f"Uploaded {progress}/{len(records)} chunks...")
        if uploaded == len(records) and uploaded % 50:
            print(f"Uploaded {uploaded}/{len(records)} chunks...")

    print("All documents were uploaded to Pinecone.")


if __name__ == "__main__":
    store_hybrid_data()
