#!/usr/bin/env python3
"""
Bot Telegram avec Google Drive - Version simple pour commencer
"""

import os
import pickle
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import PyPDF2
import io
from dotenv import load_dotenv

# Charger les variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Vérifier la config
if not TELEGRAM_TOKEN or not MISTRAL_KEY:
    print("❌ Il manque TELEGRAM_BOT_TOKEN ou MISTRAL_API_KEY dans .env")
    exit(1)

# Initialiser Mistral
mistral_client = Mistral(api_key=MISTRAL_KEY)

# Documents en mémoire
documents_cache = {}

def get_drive_service():
    """Obtenir le service Google Drive"""
    creds = None
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ Pas d'authentification Google Drive")
            print("Lance d'abord: python setup_drive_simple.py")
            return None
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

# Initialiser Drive
drive_service = get_drive_service()

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue"""
    message = """
🤖 Salut ! Je suis ton assistant avec Google Drive !

🔧 Commandes disponibles :
/sync - Charger les documents depuis Drive
/list - Voir les documents chargés
/ask [question] - Poser une question

Ou envoie-moi directement ta question !
"""
    await update.message.reply_text(message)

# Commande /sync
async def sync_drive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Synchroniser avec Google Drive"""
    if not drive_service:
        await update.message.reply_text("❌ Google Drive non configuré")
        return
    
    if not DRIVE_FOLDER_ID:
        await update.message.reply_text("❌ Pas de dossier Drive configuré")
        return
    
    await update.message.reply_text("🔄 Synchronisation en cours...")
    
    try:
        # Lister les fichiers PDF
        results = drive_service.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/pdf'",
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            await update.message.reply_text("📂 Aucun PDF trouvé dans le dossier")
            return
        
        # Charger chaque PDF
        loaded = 0
        for file in files:
            try:
                # Télécharger le fichier
                request = drive_service.files().get_media(fileId=file['id'])
                file_data = io.BytesIO()
                downloader = io.http.MediaIoBaseDownload(file_data, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                # Extraire le texte
                file_data.seek(0)
                pdf_reader = PyPDF2.PdfReader(file_data)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                # Stocker en cache
                documents_cache[file['name']] = text
                loaded += 1
                
            except Exception as e:
                print(f"Erreur avec {file['name']}: {e}")
        
        await update.message.reply_text(
            f"✅ Synchronisation terminée !\n"
            f"📚 {loaded} documents chargés"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# Commande /list
async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lister les documents chargés"""
    if not documents_cache:
        await update.message.reply_text("📂 Aucun document chargé\nUtilise /sync d'abord !")
        return
    
    message = "📚 Documents disponibles :\n\n"
    for doc_name in documents_cache.keys():
        message += f"• {doc_name}\n"
    
    await update.message.reply_text(message)

# Répondre aux questions
async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répondre en utilisant les documents"""
    question = update.message.text
    
    if question.startswith("/ask"):
        question = question[4:].strip()
    
    if not question:
        await update.message.reply_text("❓ Pose-moi une question !")
        return
    
    await update.message.reply_text("🤔 Je cherche dans les documents...")
    
    try:
        # Construire le contexte avec les documents
        if documents_cache:
            context_text = "Voici les documents disponibles :\n\n"
            
            for doc_name, content in documents_cache.items():
                # Limiter la taille du contexte
                preview = content[:2000] + "..." if len(content) > 2000 else content
                context_text += f"[Document: {doc_name}]\n{preview}\n\n"
            
            prompt = f"""Tu es un assistant qui répond aux questions en te basant sur ces documents.
            
{context_text}

Question: {question}

Réponds en te basant sur les documents fournis. Si l'information n'est pas dans les documents, dis-le."""
        else:
            prompt = f"""Tu es un assistant. L'utilisateur demande : {question}

Aucun document n'est chargé. Suggère d'utiliser /sync pour charger des documents depuis Google Drive."""
        
        # Demander à Mistral
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        await update.message.reply_text(response.choices[0].message.content)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# Fonction principale
def main():
    """Démarrer le bot"""
    print("🚀 Démarrage du bot avec Google Drive...")
    
    if not drive_service:
        print("⚠️  Google Drive non configuré - certaines fonctions seront limitées")
    
    # Créer l'application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Ajouter les commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sync", sync_drive))
    app.add_handler(CommandHandler("list", list_docs))
    app.add_handler(CommandHandler("ask", answer_question))
    
    # Messages texte
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))
    
    # Démarrer
    print("✅ Bot démarré ! Va sur Telegram")
    app.run_polling()

if __name__ == "__main__":
    main()