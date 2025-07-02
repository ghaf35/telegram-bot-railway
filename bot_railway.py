#!/usr/bin/env python3
"""
Bot Telegram optimisé pour Railway
"""

import os
import sys
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
import PyPDF2
import io

# PAS de dotenv sur Railway !

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - Railway utilise les variables d'environnement
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ghaf35/mes-cours")

# Vérifier la config
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN manquant !")
    sys.exit(1)

if not MISTRAL_KEY:
    logger.error("❌ MISTRAL_API_KEY manquant !")
    sys.exit(1)

logger.info(f"✅ Configuration OK - Repo: {GITHUB_REPO}")

# Initialiser Mistral
try:
    mistral_client = Mistral(api_key=MISTRAL_KEY)
    logger.info("✅ Mistral initialisé")
except Exception as e:
    logger.error(f"❌ Erreur Mistral: {e}")
    sys.exit(1)

# Cache des documents
documents_cache = {}

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue"""
    logger.info(f"Commande /start de {update.effective_user.username}")
    message = """
🤖 Salut ! Je peux lire tes documents sur GitHub !

📚 Comment ça marche :
1. Crée un repo GitHub avec tes PDF/TXT
2. Configure GITHUB_REPO dans .env
3. Utilise /sync pour charger les docs

🔧 Commandes :
/sync - Charger les documents
/list - Voir les documents
/help - Aide GitHub

Pose-moi tes questions ! 💬
"""
    await update.message.reply_text(message)

# Commande /help
async def help_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aide pour configurer GitHub"""
    help_text = f"""
📝 Configuration actuelle :
Repository : {GITHUB_REPO}

Pour changer de repo, mets à jour la variable GITHUB_REPO dans Railway !
"""
    await update.message.reply_text(help_text)

# Commande /sync
async def sync_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Synchroniser avec GitHub"""
    logger.info("Synchronisation GitHub demandée")
    await update.message.reply_text(f"🔄 Synchronisation avec GitHub ({GITHUB_REPO})...")
    
    try:
        # Headers pour l'API GitHub
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Récupérer la liste des fichiers
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Erreur GitHub : {response.status_code}\n"
                "Vérifie que le repo existe et est public !"
            )
            return
        
        files = response.json()
        loaded = 0
        
        # Charger chaque fichier
        for file in files:
            if file['name'].endswith(('.pdf', '.txt', '.md')):
                try:
                    # Télécharger le fichier
                    file_response = requests.get(file['download_url'])
                    
                    if file['name'].endswith('.pdf'):
                        # Lire le PDF
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_response.content))
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                    else:
                        # Fichier texte
                        text = file_response.text
                    
                    # Stocker en cache
                    documents_cache[file['name']] = text
                    loaded += 1
                    logger.info(f"Document chargé : {file['name']}")
                    
                except Exception as e:
                    logger.error(f"Erreur avec {file['name']}: {e}")
        
        await update.message.reply_text(
            f"✅ Synchronisation terminée !\n"
            f"📚 {loaded} documents chargés\n"
            f"Utilise /list pour voir les documents"
        )
        
    except Exception as e:
        logger.error(f"Erreur sync: {e}")
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# Commande /list
async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lister les documents"""
    if not documents_cache:
        await update.message.reply_text(
            "📂 Aucun document chargé\n"
            "Utilise /sync d'abord !"
        )
        return
    
    message = "📚 Documents disponibles :\n\n"
    for doc_name in documents_cache.keys():
        message += f"• {doc_name}\n"
    
    message += f"\n💡 {len(documents_cache)} documents prêts !"
    await update.message.reply_text(message)

# Répondre aux questions
async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répondre en utilisant les documents"""
    question = update.message.text
    logger.info(f"Question reçue : {question[:50]}...")
    
    await update.message.reply_text("🤔 Je cherche dans tes documents...")
    
    try:
        if documents_cache:
            # Construire le contexte
            context_text = ""
            for doc_name, content in documents_cache.items():
                preview = content[:1500] + "..." if len(content) > 1500 else content
                context_text += f"\n=== Document: {doc_name} ===\n{preview}\n"
            
            prompt = f"""Tu es un assistant qui répond aux questions d'un étudiant en te basant sur ses cours.

Voici les documents disponibles :
{context_text}

Question de l'étudiant : {question}

Réponds en :
1. Te basant sur les documents fournis
2. Citant le document source
3. Étant clair et pédagogue
4. Si l'info n'est pas dans les docs, dis-le"""
            
        else:
            prompt = f"""L'utilisateur demande : {question}

Aucun document n'est chargé. Suggère d'utiliser :
1. /help pour voir la config
2. /sync pour charger les documents"""
        
        # Demander à Mistral
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        await update.message.reply_text(response.choices[0].message.content)
        
    except Exception as e:
        logger.error(f"Erreur réponse: {e}")
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# Fonction principale
def main():
    """Démarrer le bot"""
    logger.info("🚀 Démarrage du bot GitHub sur Railway...")
    logger.info(f"📚 Repository : {GITHUB_REPO}")
    
    try:
        # Créer l'application
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Ajouter les handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_github))
        app.add_handler(CommandHandler("sync", sync_github))
        app.add_handler(CommandHandler("list", list_docs))
        
        # Messages texte
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))
        
        # Démarrer
        logger.info("✅ Bot démarré ! Polling en cours...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()