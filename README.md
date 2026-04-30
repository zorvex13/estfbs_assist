# EST FBS Assistant

Assistant conversationnel RAG pour l'École Supérieure de Technologie de Fquih Ben Salah.

Le projet permet aux étudiants de poser des questions sur les documents officiels de l'EST FBS : formations, inscription, règlements, modules, informations du campus, et autres contenus indexés dans la base vectorielle.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-5A67D8)
![Groq](https://img.shields.io/badge/Groq-LLM-orange)

## Aperçu

EST FBS Assistant est une application web complète composée de :

- une interface HTML/CSS/JavaScript en un seul fichier ;
- une API FastAPI ;
- un pipeline RAG basé sur LangChain ;
- une base vectorielle Pinecone ;
- des embeddings Gemini ;
- un modèle LLM Groq ;
- une journalisation des conversations dans Supabase PostgreSQL.

L'utilisateur pose une question depuis l'interface web. Le backend récupère les passages les plus pertinents depuis Pinecone, construit un contexte, interroge le modèle Groq, puis retourne une réponse avec les sources utilisées.

## Fonctionnalités

- Interface web professionnelle en français.
- Recherche intelligente dans les documents PDF/TXT de l'école.
- Réponses générées avec contexte documentaire.
- Affichage des sources sous forme de tags.
- Indicateur de statut API en ligne/hors ligne.
- Historique court envoyé au RAG pour garder le contexte conversationnel.
- Endpoint `/health` pour vérifier l'état du service.
- Script d'indexation pour ajouter de nouveaux documents à Pinecone.
- Sauvegarde des interactions dans Supabase.

## Architecture

```text
data/*.pdf, data/*.txt
        |
        v
scripts/load_vectors.py
        |
        v
Gemini Embeddings
        |
        v
Pinecone Vector DB
        |
        v
FastAPI /ask
        |
        v
LangChain RAG + Groq LLM
        |
        v
Réponse + sources + log Supabase
```

## Stack Technique

- Python 3.11+
- FastAPI
- Uvicorn
- LangChain
- Groq LLM
- Google Gemini Embeddings
- Pinecone
- Supabase PostgreSQL
- SQLAlchemy
- HTML/CSS/JavaScript natif

## Structure du Projet

```text
est_fbs_chatbot/
├── app/
│   ├── main.py          API FastAPI, endpoints et frontend
│   ├── rag.py           Pipeline RAG et génération des réponses
│   └── database.py      Journalisation Supabase/PostgreSQL
├── data/
│   ├── *.pdf            Documents officiels à indexer
│   └── *.txt            Documents texte à indexer
├── scripts/
│   └── load_vectors.py  Chargement des documents dans Pinecone
├── index.html           Frontend chatbot en un seul fichier
├── requirements.txt     Dépendances Python
├── .env.example         Exemple de configuration
└── README.md
```

## Prérequis

Avant de lancer le projet, il faut disposer de :

- Python 3.11 ou plus récent ;
- un compte Groq ;
- une clé API Google AI Studio pour les embeddings Gemini ;
- un index Pinecone ;
- une base PostgreSQL Supabase ;
- les documents PDF/TXT à indexer dans le dossier `data/`.

## Installation

1. Cloner le projet :

```bash
git clone <repository-url>
cd est_fbs_chatbot
```

2. Créer et activer un environnement virtuel :

```bash
python -m venv venv
source venv/bin/activate
```

Sous Windows :

```bash
venv\Scripts\activate
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Configuration

Créer un fichier `.env` à la racine du projet :

```env
GOOGLE_API_KEY=your_google_ai_studio_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_pinecone_index_name_here
DATABASE_URL=your_supabase_postgres_connection_string_here
```

Le fichier `.env` est ignoré par Git pour protéger les clés API.

## Indexer les Documents

Pour ajouter ou mettre à jour les documents dans Pinecone, placer les fichiers dans `data/`, puis exécuter :

```bash
python scripts/load_vectors.py
```

Le script :

1. lit les fichiers PDF et TXT ;
2. découpe le contenu en chunks ;
3. génère les embeddings avec Gemini ;
4. envoie les vecteurs vers Pinecone.

Les documents déjà présents peuvent être réindexés. Les identifiants sont basés sur le contenu des chunks.

## Lancer l'Application

Démarrer le serveur FastAPI :

```bash
uvicorn app.main:app --reload
```

L'application sera disponible à l'adresse :

```text
http://localhost:8000
```

Le frontend est servi directement par FastAPI depuis `index.html`.

## Endpoints API

### `GET /`

Retourne l'interface web du chatbot.

### `GET /health`

Vérifie l'état de l'API et retourne les informations principales du service.

Exemple de réponse :

```json
{
  "status": "online",
  "ok": true,
  "model": "llama-3.3-70b-versatile",
  "chunk_count": 29
}
```

### `POST /ask`

Pose une question au chatbot.

Requête recommandée :

```json
{
  "question": "Quelles formations propose l'EST FBS ?"
}
```

Requête avec historique :

```json
{
  "question": "Quels sont les modules principaux ?",
  "history": [
    {
      "user": "Quelles formations propose l'EST FBS ?",
      "bot": "L'EST FBS propose..."
    }
  ]
}
```

Réponse :

```json
{
  "answer": "L'EST FBS propose des formations selon les documents indexés...",
  "reponse": "L'EST FBS propose des formations selon les documents indexés...",
  "sources": [
    "presentation.txt",
    "description_donnees_reglement_EST_FBS.pdf"
  ]
}
```

Le champ `reponse` est conservé pour compatibilité avec les premières versions du projet.

## Ajouter un Nouveau PDF

1. Copier le fichier PDF dans `data/`.
2. Lancer l'indexation :

```bash
python scripts/load_vectors.py
```

3. Redémarrer le serveur si nécessaire :

```bash
uvicorn app.main:app --reload
```

Le chatbot pourra ensuite répondre à partir du nouveau document.

## Base de Données

Les interactions utilisateur sont sauvegardées dans Supabase via SQLAlchemy.

Table utilisée :

```text
chat_logs
```

Champs principaux :

- `id`
- `timestamp`
- `question`
- `reponse`
- `sources`

## Développement

Commandes utiles :

```bash
# Vérifier la syntaxe Python
python -m py_compile app/main.py app/rag.py app/database.py

# Réindexer les documents
python scripts/load_vectors.py

# Lancer le serveur en mode développement
uvicorn app.main:app --reload
```

## Dépannage

### Le frontend affiche "hors ligne"

Vérifier que le serveur FastAPI est lancé :

```bash
uvicorn app.main:app --reload
```

### Le RAG ne démarre pas

Vérifier les variables suivantes dans `.env` :

- `GOOGLE_API_KEY`
- `GROQ_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `DATABASE_URL`

### Le chatbot ne trouve pas les informations du nouveau PDF

Relancer l'indexation :

```bash
python scripts/load_vectors.py
```

Puis redémarrer l'API si besoin.

## Sécurité

- Ne jamais commiter le fichier `.env`.
- Ne jamais exposer les clés API dans le frontend.
- Vérifier les règles d'accès Supabase/Pinecone avant un déploiement public.

## Licence

Projet réalisé dans un cadre académique pour l'EST Fquih Ben Salah.
