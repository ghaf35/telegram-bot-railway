#!/usr/bin/env python3
"""
Version simplifiée du bot pour debug - Sans synchronisation automatique
"""

import os
import sys
import logging
import requests
import json
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import PyPDF2
import io

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATPDF_KEY = os.environ.get("CHATPDF_API_KEY")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ghaf35/mes-cours")

# Vérifier la config
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN manquant !")
    sys.exit(1)

if not CHATPDF_KEY:
    logger.error("❌ CHATPDF_API_KEY manquant ! Le bot a besoin de ChatPDF pour fonctionner.")
    sys.exit(1)

logger.info(f"✅ Configuration OK - Repo: {GITHUB_REPO}")
logger.info("✅ ChatPDF API Key détectée")

# Cache des documents
documents_cache = {}
chatpdf_sources = {}

# Commande /start simple
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue simple"""
    message = """
🤖 *Bot de test simplifié*

Tape `/sync` pour charger les documents
Puis pose tes questions !
"""
    await update.message.reply_text(message, parse_mode='Markdown')

# Commande /sync simple
async def sync_simple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Synchronisation simple pour test"""
    await update.message.reply_text("🔄 Synchronisation...", parse_mode='Markdown')
    
    try:
        # Test simple - charger un document
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
        response = requests.get(url)
        
        if response.status_code == 200:
            await update.message.reply_text(
                f"✅ GitHub accessible ! {len(response.json())} fichiers trouvés",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Erreur GitHub : {response.status_code}",
                parse_mode='Markdown'
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur : {str(e)}",
            parse_mode='Markdown'
        )

# Question simple
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répondre aux messages"""
    question = update.message.text
    await update.message.reply_text(
        f"🤖 Tu as dit : {question}\n\n"
        "Je suis en mode test simplifié !",
        parse_mode='Markdown'
    )

def main():
    """Démarrer le bot simplifié"""
    logger.info("🚀 Démarrage du bot simplifié...")
    
    try:
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("sync", sync_simple))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Bot simplifié démarré !")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Erreur : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()