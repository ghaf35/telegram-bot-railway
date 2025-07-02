#!/usr/bin/env python3
"""
Bot Telegram qui lit des documents depuis un dossier local
"""

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
import PyPDF2
from dotenv import load_dotenv

# Charger les variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")
DOCS_FOLDER = "mes_documents"  # Dossier local avec tes fichiers

# Créer le dossier s'il n'existe pas
os.makedirs(DOCS_FOLDER, exist_ok=True)

# Initialiser Mistral
mistral_client = Mistral(api_key=MISTRAL_KEY)

# Cache des documents
documents_cache = {}

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """
🤖 Bot avec documents locaux !

📁 Mets tes PDF/TXT dans le dossier 'mes_documents'

🔧 Commandes :
/sync - Charger les documents
/list - Voir les documents
/folder - Voir où mettre les fichiers

Pose tes questions ! 💬
"""
    await update.message.reply_text(message)

# Commande /folder
async def show_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    folder_path = os.path.abspath(DOCS_FOLDER)
    await update.message.reply_text(
        f"📁 Mets tes fichiers ici :\n{folder_path}\n\n"
        "Puis lance /sync !"
    )

# Commande /sync
async def sync_local(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Chargement des documents...")
    
    loaded = 0
    documents_cache.clear()
    
    for filename in os.listdir(DOCS_FOLDER):
        file_path = os.path.join(DOCS_FOLDER, filename)
        
        try:
            if filename.endswith('.pdf'):
                # Lire PDF
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                documents_cache[filename] = text
                loaded += 1
                
            elif filename.endswith(('.txt', '.md')):
                # Lire texte
                with open(file_path, 'r', encoding='utf-8') as file:
                    documents_cache[filename] = file.read()
                loaded += 1
                
        except Exception as e:
            print(f"Erreur avec {filename}: {e}")
    
    await update.message.reply_text(
        f"✅ {loaded} documents chargés !\n"
        "Pose tes questions maintenant !"
    )

# Commande /list
async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not documents_cache:
        await update.message.reply_text("📂 Aucun document chargé")
        return
    
    message = "📚 Documents disponibles :\n\n"
    for doc in documents_cache.keys():
        message += f"• {doc}\n"
    await update.message.reply_text(message)

# Répondre aux questions
async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await update.message.reply_text("🤔 Je réfléchis...")
    
    try:
        if documents_cache:
            context_text = ""
            for doc_name, content in documents_cache.items():
                preview = content[:1000] + "..." if len(content) > 1000 else content
                context_text += f"\n[{doc_name}]\n{preview}\n"
            
            prompt = f"""Réponds à cette question en te basant sur ces documents :
{context_text}

Question : {question}"""
        else:
            prompt = f"Pas de documents chargés. Dis à l'utilisateur d'utiliser /sync. Question : {question}"
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        
        await update.message.reply_text(response.choices[0].message.content)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

def main():
    print(f"🚀 Bot démarré !")
    print(f"📁 Dossier documents : {os.path.abspath(DOCS_FOLDER)}")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("folder", show_folder))
    app.add_handler(CommandHandler("sync", sync_local))
    app.add_handler(CommandHandler("list", list_docs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))
    
    app.run_polling()

if __name__ == "__main__":
    main()