import chainlit as cl
import requests
import os

# L'adresse de ton cerveau (FastAPI)
API_URL = "http://localhost:8000/ask"

@cl.on_chat_start
async def demarrer_chat():
    # 1. Initialiser la mémoire (Historique)
    cl.user_session.set("chat_history", [])
    
    # 2. Gestion du Logo (avec taille contrôlée)
    logo_path = "src/web_api/public/logo.png"
    elements = []
    
    if os.path.exists(logo_path):
        elements = [
            cl.Image(
                path=logo_path, 
                name="logo_est", 
                display="inline", 
                size="medium"  # Empêche le logo d'être trop grand
            )
        ]

    # 3. Message de bienvenue pro
    await cl.Message(
        content="✨ **Bienvenue sur l'Assistant Officiel de l'EST FBS** ✨\n\nJe suis là pour vous aider à trouver des informations sur les filières, les bourses ou le règlement intérieur. Que souhaitez-vous savoir ?",
        elements=elements
    ).send()

@cl.on_message
async def traiter_message(message: cl.Message):
    # Récupérer l'historique
    history = cl.user_session.get("chat_history")
    
    # Message d'attente
    msg = cl.Message(content="⏳ *Recherche dans les documents officiels...*")
    await msg.send()

    try:
        # Envoi à FastAPI (Texte + 6 derniers messages de mémoire)
        payload = {
            "text": message.content,
            "history": history[-6:]
        }
        
        reponse_serveur = requests.post(API_URL, json=payload, timeout=30)
        reponse_serveur.raise_for_status()
        
        data = reponse_serveur.json()
        texte_ia = data.get("reponse", "Désolé, je ne trouve pas d'information à ce sujet.")
        sources = data.get("sources", [])
        
        # Mise à jour de la mémoire
        history.append({"role": "Étudiant", "content": message.content})
        history.append({"role": "Assistant", "content": texte_ia})
        cl.user_session.set("chat_history", history)

        # Affichage final avec sources
        res = texte_ia
        if sources:
            res += f"\n\n---\n📚 **Sources :** *{', '.join(sources)}*"
        
        msg.content = res
        await msg.update()
        
    except Exception as e:
        msg.content = f"❌ **Erreur :** Impossible de joindre le cerveau (FastAPI). Vérifie qu'il est lancé sur le port 8000.\n*(Détail: {e})*"
        await msg.update()