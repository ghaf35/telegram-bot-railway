#!/usr/bin/env python3
"""
Bot Telegram qui lit des documents depuis des URLs
"""

import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
import PyPDF2
import io
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")

mistral_client = Mistral(api_key=MISTRAL_KEY)
documents_cache = {}

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """
🤖 Bot qui lit des documents depuis des URLs !

📎 Comment ça marche :
/add [URL] - Ajouter un document
/list - Voir les documents
/clear - Effacer tout

Exemple :
/add https://exemple.com/cours.pdf

Pose tes questions ! 💬
"""
    await update.message.reply_text(message)

# Commande /add
async def add_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Donne-moi une URL !\nExemple : /add https://site.com/doc.pdf")
        return
    
    url = context.args[0]
    await update.message.reply_text(f"📥 Téléchargement de {url}...")
    
    try:
        response = requests.get(url)
        filename = url.split('/')[-1]
        
        if url.endswith('.pdf'):
            # Lire PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(response.content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        else:
            # Texte brut
            text = response.text
        
        documents_cache[filename] = text
        await update.message.reply_text(f"✅ Document '{filename}' ajouté !")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# Les autres commandes...
async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not documents_cache:
        await update.message.reply_text("📂 Aucun document")
        return
    
    message = "📚 Documents :\n"
    for doc in documents_cache.keys():
        message += f"• {doc}\n"
    await update.message.reply_text(message)

async def clear_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    documents_cache.clear()
    await update.message.reply_text("🗑️ Documents effacés !")

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await update.message.reply_text("🤔 Je cherche...")
    
    try:
        if documents_cache:
            context_text = ""
            for doc_name, content in documents_cache.items():
                preview = content[:1000]
                context_text += f"\n[{doc_name}]\n{preview}\n"
            
            prompt = f"Réponds en te basant sur ces documents :\n{context_text}\n\nQuestion : {question}"
        else:
            prompt = f"Pas de documents. Dis d'utiliser /add [URL]. Question : {question}"
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        
        await update.message.reply_text(response.choices[0].message.content)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

def main():
    print("🚀 Bot URL démarré !")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_url))
    app.add_handler(CommandHandler("list", list_docs))
    app.add_handler(CommandHandler("clear", clear_docs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))
    
    app.run_polling()

if __name__ == "__main__":
    main()