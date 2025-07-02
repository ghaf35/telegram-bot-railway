#!/usr/bin/env python3
"""
Bot Telegram simple pour commencer !
"""

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")

# Vérifier la configuration
if not TELEGRAM_TOKEN:
    print("❌ ERREUR: Il manque TELEGRAM_BOT_TOKEN dans le fichier .env")
    print("👉 Ouvre .env et ajoute: TELEGRAM_BOT_TOKEN=ton_token_ici")
    exit(1)

if not MISTRAL_KEY:
    print("❌ ERREUR: Il manque MISTRAL_API_KEY dans le fichier .env")
    print("👉 Ouvre .env et ajoute: MISTRAL_API_KEY=ta_clé_ici")
    exit(1)

# Initialiser Mistral
client = Mistral(api_key=MISTRAL_KEY)

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue"""
    message = """
🤖 Salut ! Je suis ton assistant IA !

Tu peux me poser n'importe quelle question et je ferai de mon mieux pour t'aider !

Exemples:
- Explique-moi les maths
- Comment coder en Python ?
- Raconte-moi une blague

Envoie-moi ta question ! 💬
"""
    await update.message.reply_text(message)

# Répondre aux messages
async def repondre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répondre aux questions avec l'IA"""
    # Récupérer la question
    question = update.message.text
    
    # Message d'attente
    await update.message.reply_text("🤔 Je réfléchis...")
    
    try:
        # Demander à l'IA Mistral
        messages = [
            {"role": "system", "content": "Tu es un assistant amical qui aide un adolescent. Réponds de manière simple et claire."},
            {"role": "user", "content": question}
        ]
        
        response = client.chat.complete(
            model="mistral-small-latest",  # Modèle économique et efficace
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        # Récupérer la réponse
        reponse = response.choices[0].message.content
        
        # Envoyer la réponse
        await update.message.reply_text(reponse)
        
    except Exception as e:
        # En cas d'erreur
        await update.message.reply_text(
            "😕 Désolé, j'ai eu un problème. Vérifie ta connexion et réessaie !"
        )
        print(f"Erreur: {e}")

# Fonction principale
def main():
    """Démarrer le bot"""
    print("🚀 Démarrage du bot...")
    
    # Créer l'application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Ajouter les commandes
    app.add_handler(CommandHandler("start", start))
    
    # Répondre à tous les messages texte
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, repondre))
    
    # Démarrer
    print("✅ Bot démarré ! Va sur Telegram pour le tester")
    print("Pour arrêter: Ctrl+C")
    app.run_polling()

if __name__ == "__main__":
    main()