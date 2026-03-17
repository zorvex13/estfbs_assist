import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Charger les clés secrètes
load_dotenv()

# 2. Initialiser l'application Web (API)
app = FastAPI(
    title="API Chatbot EST FBS",
    description="Le moteur RAG du PFE, accessible via requêtes HTTP.",
    version="1.0"
)

# 3. Définir le format de la question (Ce que le Frontend va envoyer)
class Question(BaseModel):
    text: str

# 4. Préparer le Cerveau IA (Chargé une seule fois au démarrage du serveur)
print("⏳ Démarrage du moteur IA LangChain...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
index_name = os.getenv("PINECONE_INDEX_NAME")
vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

template = """Tu es l'assistant virtuel officiel de l'EST Fquih Ben Salah (EST FBS).
Ton rôle est d'aider les étudiants en répondant à leurs questions.
Utilise UNIQUEMENT le contexte fourni ci-dessous pour répondre.
Si la réponse ne s'y trouve pas, dis poliment que tu ne sais pas.

Contexte :
{context}

Question : {question}
Réponse :"""

prompt = ChatPromptTemplate.from_template(template)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
print("✅ Moteur IA prêt et connecté à Pinecone !")

# ==========================================================
# 5. LES ROUTES DE L'API (Les portes d'entrée du serveur)
# ==========================================================

@app.get("/")
def home():
    return {"message": "Bienvenue sur l'API du Chatbot EST FBS. Le serveur est en ligne."}

@app.post("/ask")
def poser_question(q: Question):
    print(f"📥 Nouvelle question reçue depuis le site web : {q.text}")
    
    # A. Chercher les documents sources
    sources_docs = retriever.invoke(q.text)
    noms_sources = list(set([os.path.basename(doc.metadata.get('source', 'Inconnue')) for doc in sources_docs]))
    
    # B. Générer la réponse avec l'IA
    reponse_ia = rag_chain.invoke(q.text)
    
    # C. Renvoyer le paquet propre (JSON) au site web
    return {
        "reponse": reponse_ia,
        "sources": noms_sources
    }

# 6. Lancement du serveur
if __name__ == "__main__":
    print("🚀 Lancement du serveur web sur le port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)