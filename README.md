# Bot Telegram RAG avec Google Drive

Un bot Telegram intelligent qui répond aux questions en se basant sur des documents stockés dans Google Drive.

## 🚀 Fonctionnalités

- 📁 Synchronisation automatique avec Google Drive
- 🤖 Réponses basées sur vos documents (PDF, DOCX, TXT)
- 🔍 Recherche sémantique avec RAG (Retrieval-Augmented Generation)
- 💬 Interface conversationnelle via Telegram
- 🧠 Support de plusieurs LLMs (OpenAI, Anthropic, Mistral)
- 💾 Indexation vectorielle persistante (FAISS/Chroma)

## 📋 Prérequis

- Python 3.9+
- Compte Google avec accès Drive
- Bot Telegram (créé via @BotFather)
- Clé API pour un LLM (OpenAI, Anthropic ou Mistral)

## 🛠️ Installation

1. **Cloner le projet**
```bash
cd telegram-rag-bot
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration**
```bash
cp .env.example .env
```

Éditer `.env` avec vos clés:
- `TELEGRAM_BOT_TOKEN`: Token de votre bot Telegram
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `MISTRAL_API_KEY`: Clé API du LLM
- `LLM_PROVIDER`: openai, anthropic ou mistral
- `LLM_MODEL`: Modèle à utiliser

4. **Configuration Google Drive**
```bash
python setup_google_auth.py
```

Suivre les instructions pour:
- Créer les credentials OAuth2 sur Google Cloud Console
- Autoriser l'accès à votre Drive
- Configurer le dossier à synchroniser

## 🚀 Utilisation

1. **Démarrer le bot**
```bash
python main.py
```

2. **Commandes Telegram**
- `/start` - Message de bienvenue
- `/sync` - Synchroniser les documents depuis Drive
- `/ask [question]` - Poser une question
- `/status` - Voir le statut du bot
- Ou envoyez directement votre question!

## 📁 Structure du projet

```
telegram-rag-bot/
├── main.py                 # Point d'entrée du bot
├── config.py              # Configuration
├── services/
│   ├── google_drive.py    # Intégration Google Drive
│   ├── document_processor.py  # Extraction de texte
│   ├── rag_engine.py      # Moteur RAG et indexation
│   └── llm_service.py     # Service LLM
├── requirements.txt       # Dépendances
├── .env.example          # Template de configuration
└── setup_google_auth.py  # Script de configuration Drive
```

## 🔧 Configuration avancée

### Base vectorielle
- `VECTOR_DB_TYPE`: faiss (rapide) ou chroma (plus de fonctionnalités)
- `CHUNK_SIZE`: Taille des segments de texte (défaut: 1000)
- `CHUNK_OVERLAP`: Chevauchement entre segments (défaut: 200)

### Formats supportés
- PDF (avec extraction de tableaux)
- DOCX (Word)
- TXT

## 🐛 Dépannage

**Le bot ne trouve pas mes documents**
- Vérifier que les fichiers sont dans le bon dossier Drive
- Relancer `/sync` après ajout de nouveaux fichiers

**Erreur d'authentification Google**
- Supprimer `token.json` et relancer `setup_google_auth.py`
- Vérifier que l'API Drive est activée dans Google Cloud Console

**Réponses lentes**
- Réduire `CHUNK_SIZE` pour des documents plus petits
- Utiliser FAISS au lieu de Chroma pour plus de rapidité

## 🔒 Sécurité

- Les tokens sont stockés localement dans `.env`
- L'authentification Google utilise OAuth2
- Les documents restent privés sur votre Drive
- Le bot n'a qu'un accès en lecture seule

## 📝 License

MIT