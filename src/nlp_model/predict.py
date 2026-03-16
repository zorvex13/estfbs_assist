import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Charger les clés
load_dotenv()

def lancer_chatbot():
    print("⏳ Réveil du Chatbot EST FBS (Architecture LCEL)...")

    # 2. Configurer le Cerveau (Embeddings et Base de données)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    
    # Le "Chercheur" qui va fouiller dans tes PDF
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # 3. Configurer l'IA qui va parler
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

    # 4. Créer la personnalité (Le Prompt)
    template = """Tu es l'assistant virtuel officiel de l'EST Fquih Ben Salah (EST FBS).
    Ton rôle est d'aider les étudiants en répondant à leurs questions.
    Utilise UNIQUEMENT le contexte fourni ci-dessous pour répondre.
    Si la réponse ne s'y trouve pas, dis poliment que tu ne sais pas et conseille de contacter l'administration.
    
    Contexte extrait des documents :
    {context}
    
    Question de l'étudiant : {question}
    Réponse :"""
    
    prompt = ChatPromptTemplate.from_template(template)

    # 5. Fonction pour nettoyer le texte trouvé
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # 6. LA NOUVELLE ARCHITECTURE (LCEL) - Plus de bug "chains" !
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("✅ Chatbot prêt ! (Tape 'quit' pour quitter)\n")
    print("-" * 50)

    # 7. La boucle de conversation
    while True:
        question = input("🧑‍🎓 Toi : ")
        if question.lower() == 'quit':
            print("👋 Au revoir !")
            break
            
        print("🤖 Bot en train de lire les documents...")
        
        # A. On cherche les sources en premier (pour les afficher)
        sources = retriever.invoke(question)
        
        # B. On génère la réponse finale
        reponse = rag_chain.invoke(question)
        
        print(f"\n🎓 EST FBS Bot : {reponse}")
        
        print("\n   [Sources consultées :]")
        # Utilisation d'un "set" pour ne pas afficher 3 fois le même nom de fichier
        noms_sources = set([os.path.basename(doc.metadata.get('source', 'Source inconnue')) for doc in sources])
        for source in noms_sources:
            print(f"   - {source}")
        print("-" * 50)

if __name__ == "__main__":
    lancer_chatbot()