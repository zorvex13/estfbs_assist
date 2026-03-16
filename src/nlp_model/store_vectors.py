import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone

load_dotenv()

def store_hybrid_data():
    raw_data_path = "data/raw/"
    all_chunks = []

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    for file in os.listdir(raw_data_path):
        file_path = os.path.join(raw_data_path, file)
        
        if file.endswith(".pdf"):
            print(f" Lecture du PDF : {file}")
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            all_chunks.extend(text_splitter.split_documents(docs))
            
        elif file.endswith(".txt"):
            print(f"Lecture du TXT : {file}")
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
            all_chunks.extend(text_splitter.split_documents(docs))

    # Connexion Cloud
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

    print(f"Vectorisation de {len(all_chunks)} morceaux...")
    
    for i, chunk in enumerate(all_chunks):
        vector = embeddings.embed_query(chunk.page_content)
        
        # Metadata : On garde le texte et la source
        metadata = {
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", "Unknown")
        }
        
        index.upsert(vectors=[(f"doc_{i}", vector, metadata)])

    print("Tout est dans le Cloud !")

if __name__ == "__main__":
    store_hybrid_data()