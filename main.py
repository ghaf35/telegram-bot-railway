#!/usr/bin/env python3

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config
from services.google_drive import GoogleDriveService
from services.document_processor import DocumentProcessor
from services.rag_engine import RAGEngine
from services.llm_service import LLMService

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramRAGBot:
    def __init__(self):
        self.config = Config()
        self.drive_service = GoogleDriveService()
        self.doc_processor = DocumentProcessor()
        self.rag_engine = RAGEngine()
        self.llm_service = LLMService()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        welcome_message = """
🤖 Bienvenue sur le Bot RAG Telegram!

Je peux répondre à vos questions en me basant sur les documents stockés dans Google Drive.

Commandes disponibles:
/start - Afficher ce message
/sync - Synchroniser les documents depuis Google Drive
/ask [votre question] - Poser une question
/status - Voir le statut du bot

Ou envoyez-moi directement votre question!
        """
        await update.message.reply_text(welcome_message)
    
    async def sync_documents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /sync pour synchroniser les documents"""
        await update.message.reply_text("🔄 Synchronisation des documents en cours...")
        
        try:
            # Récupérer les fichiers depuis Google Drive
            files = await self.drive_service.list_files()
            await update.message.reply_text(f"📁 {len(files)} fichiers trouvés")
            
            # Traiter chaque fichier
            processed = 0
            for file in files:
                try:
                    # Télécharger le fichier
                    content = await self.drive_service.download_file(file['id'])
                    
                    # Extraire le texte
                    text = await self.doc_processor.extract_text(content, file['name'])
                    
                    # Indexer dans la base vectorielle
                    await self.rag_engine.add_document(text, file['name'], file['id'])
                    
                    processed += 1
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de {file['name']}: {e}")
            
            await update.message.reply_text(
                f"✅ Synchronisation terminée! {processed}/{len(files)} documents indexés."
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {e}")
            await update.message.reply_text(
                "❌ Erreur lors de la synchronisation. Vérifiez les logs."
            )
    
    async def ask_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Répondre aux questions des utilisateurs"""
        question = update.message.text
        
        # Retirer la commande /ask si présente
        if question.startswith("/ask"):
            question = question[4:].strip()
        
        if not question:
            await update.message.reply_text("❓ Veuillez poser une question!")
            return
        
        await update.message.reply_text("🤔 Je réfléchis...")
        
        try:
            # Rechercher les documents pertinents
            relevant_docs = await self.rag_engine.search(question)
            
            if not relevant_docs:
                await update.message.reply_text(
                    "😕 Je n'ai trouvé aucun document pertinent pour répondre à votre question."
                )
                return
            
            # Générer la réponse avec le LLM
            answer = await self.llm_service.generate_answer(question, relevant_docs)
            
            # Formater la réponse
            response = f"📝 **Réponse:**\n\n{answer}\n\n"
            response += "📚 **Sources:**\n"
            for doc in relevant_docs[:3]:  # Limiter à 3 sources
                response += f"• {doc['metadata']['source']}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la question: {e}")
            await update.message.reply_text(
                "❌ Une erreur s'est produite lors du traitement de votre question."
            )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /status"""
        try:
            doc_count = await self.rag_engine.get_document_count()
            status_message = f"""
📊 **Statut du Bot**

✅ Bot actif
📄 Documents indexés: {doc_count}
🤖 Modèle LLM: {self.config.LLM_MODEL}
💾 Base vectorielle: {self.config.VECTOR_DB_TYPE}
            """
            await update.message.reply_text(status_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            await update.message.reply_text("❌ Erreur lors de la récupération du statut")
    
    def run(self):
        """Démarrer le bot"""
        # Créer l'application
        application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Ajouter les handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("sync", self.sync_documents))
        application.add_handler(CommandHandler("ask", self.ask_question))
        application.add_handler(CommandHandler("status", self.status))
        
        # Handler pour les messages texte
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.ask_question
        ))
        
        # Démarrer le bot
        logger.info("Bot démarré!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = TelegramRAGBot()
    bot.run()