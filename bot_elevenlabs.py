#!/usr/bin/env python3
"""
Bot Telegram avec synthèse vocale ElevenLabs
"""

import os
import sys
import logging
import requests
import tempfile
import io
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
import PyPDF2
from elevenlabs import VoiceSettings, play, save
from elevenlabs.client import ElevenLabs

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.environ.get("ELEVENLABS_AGENT_ID")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ghaf35/mes-cours")

# Vérifier la config
if not all([TELEGRAM_TOKEN, MISTRAL_KEY, ELEVENLABS_API_KEY]):
    logger.error("❌ Variables manquantes ! Vérifie TELEGRAM_BOT_TOKEN, MISTRAL_API_KEY et ELEVENLABS_API_KEY")
    sys.exit(1)

logger.info(f"✅ Configuration OK - Repo: {GITHUB_REPO}")
logger.info(f"✅ ElevenLabs API Key: {ELEVENLABS_API_KEY[:10]}...") # Affiche les 10 premiers caractères
logger.info(f"✅ Agent ID: {ELEVENLABS_AGENT_ID if ELEVENLABS_AGENT_ID else 'Non défini'}")

# Initialiser les clients
try:
    mistral_client = Mistral(api_key=MISTRAL_KEY)
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    logger.info("✅ Mistral et ElevenLabs initialisés")
except Exception as e:
    logger.error(f"❌ Erreur initialisation: {e}")
    sys.exit(1)

# Cache des documents
documents_cache = {}

# Fonction pour générer de l'audio avec ElevenLabs
async def generate_audio(text: str, voice_id: str = None) -> bytes:
    """Générer un audio à partir du texte avec ElevenLabs"""
    try:
        # Utiliser l'agent ID si disponible, sinon la voix par défaut
        if ELEVENLABS_AGENT_ID:
            voice_id = ELEVENLABS_AGENT_ID
        elif not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice par défaut
        
        logger.info(f"Génération audio avec voice_id: {voice_id}")
        # Nettoyer le texte des emojis et markdown
        clean_text = text.replace("*", "").replace("_", "").replace("`", "")
        # Garder seulement les caractères ASCII et français
        clean_text = ''.join(char for char in clean_text if ord(char) < 128 or char in 'àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ')
        
        # Limiter la longueur (ElevenLabs a une limite)
        if len(clean_text) > 2500:
            clean_text = clean_text[:2500] + "..."
        
        logger.info(f"Texte à convertir ({len(clean_text)} caractères): {clean_text[:100]}...")
        
        # Utiliser le SDK ElevenLabs correctement
        try:
            # Générer l'audio avec le SDK
            audio_generator = elevenlabs_client.text_to_speech.convert(
                text=clean_text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            # Convertir en bytes
            audio_bytes = b"".join(audio_generator)
            logger.info("Audio généré avec succès via SDK")
            return audio_bytes
            
        except Exception as sdk_error:
            logger.error(f"Erreur SDK ElevenLabs: {str(sdk_error)}")
            # Fallback sur l'API HTTP si le SDK échoue
            import httpx
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            data = {
                "text": clean_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("Audio généré avec succès via HTTP")
                    return response.content
                else:
                    logger.error(f"Erreur API ElevenLabs: {response.status_code}")
                    logger.error(f"Réponse: {response.text}")
                    return None
        
    except Exception as e:
        logger.error(f"Erreur génération audio ElevenLabs: {str(e)}")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Voice ID utilisé: {voice_id}")
        return None

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue avec audio"""
    logger.info(f"Commande /start de {update.effective_user.username}")
    
    message = """
🤖 *Salut ! Je suis ton assistant intelligent avec voix !*

Je peux lire tes documents et te répondre en audio 🎧

━━━━━━━━━━━━━━━━━━━━━

🎯 *Nouvelles commandes vocales :*
• `/explain_audio [concept]` → Explication audio
• `/summary_audio [doc]` → Résumé vocal
• `/read [doc]` → Lecture du document

🔊 *Autres commandes :*
• `/voice on/off` → Activer/désactiver la voix
• `/sync` → Charger tes documents
• Toutes les commandes classiques !

━━━━━━━━━━━━━━━━━━━━━

💬 *Essaie :* `/explain_audio photosynthèse`
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')
    
    # Envoyer un message de bienvenue audio
    welcome_audio = await generate_audio(
        "Salut ! Je suis ton assistant intelligent avec synthèse vocale. "
        "Je peux t'expliquer tes cours et te faire des résumés audio. "
        "Essaie la commande explain audio pour commencer !"
    )
    
    if welcome_audio:
        await update.message.reply_voice(
            voice=welcome_audio,
            caption="🎧 *Message de bienvenue*",
            parse_mode='Markdown'
        )

# Commande /explain_audio
async def explain_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Expliquer un concept avec audio"""
    if not context.args:
        await update.message.reply_text(
            "🎧 *Utilisation :* `/explain_audio [concept]`\n\n"
            "Exemples :\n"
            "• `/explain_audio photosynthèse`\n"
            "• `/explain_audio développement durable`",
            parse_mode='Markdown'
        )
        return
    
    concept = ' '.join(context.args)
    logger.info(f"Explication audio demandée pour : {concept}")
    
    # Message d'attente
    processing_msg = await update.message.reply_text(
        f"🎤 *Génération de l'explication audio pour :* `{concept}`\n\n"
        "⏳ _Préparation en cours..._",
        parse_mode='Markdown'
    )
    
    try:
        # Chercher le concept dans les documents
        context_text = ""
        if documents_cache:
            for doc_name, content in documents_cache.items():
                if concept.lower() in content.lower():
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if concept.lower() in line.lower():
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            context_text += '\n'.join(lines[start:end]) + "\n\n"
                            if len(context_text) > 1000:
                                break
                if len(context_text) > 1000:
                    break
        
        # Générer l'explication avec Mistral
        prompt = f"""Explique le concept "{concept}" de manière simple et claire pour un élève.
        
{("Contexte trouvé : " + context_text) if context_text else "Utilise tes connaissances générales."}

IMPORTANT : 
- Fais une explication orale, comme si tu parlais à l'élève
- Pas de formatage markdown, pas d'astérisques
- Utilise un langage simple et des exemples concrets
- Maximum 3-4 phrases courtes et claires"""

        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3
        )
        
        explanation = response.choices[0].message.content
        
        # Générer l'audio
        audio_bytes = await generate_audio(explanation)
        
        if audio_bytes:
            # Mettre à jour le message
            await processing_msg.edit_text(
                f"✅ *Explication audio de :* `{concept}`\n\n"
                f"📝 _Transcription :_\n{explanation}",
                parse_mode='Markdown'
            )
            
            # Envoyer l'audio
            await update.message.reply_voice(
                voice=audio_bytes,
                caption=f"🎧 *{concept}*",
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(
                "❌ *Erreur de génération audio*\n\n"
                f"📝 *Explication texte :*\n{explanation}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Erreur explain_audio: {e}")
        await processing_msg.edit_text(
            "❌ *Erreur lors de la génération*\n\n"
            "_Essaie avec `/explain` pour la version texte_",
            parse_mode='Markdown'
        )

# Commande /summary_audio
async def summary_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Résumer un document en audio"""
    if not documents_cache:
        await update.message.reply_text(
            "📂 *Aucun document disponible*\n\n"
            "Utilise `/sync` pour charger des documents !",
            parse_mode='Markdown'
        )
        return
    
    if not context.args:
        message = "🎧 *Utilisation :* `/summary_audio [nom du document]`\n\n"
        message += "*Documents disponibles :*\n"
        for doc_name in list(documents_cache.keys())[:5]:
            emoji = "📕" if doc_name.endswith('.pdf') else "📄"
            message += f"{emoji} `{doc_name}`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    # Trouver le document
    doc_name = ' '.join(context.args)
    found_doc = None
    for name in documents_cache.keys():
        if doc_name.lower() in name.lower():
            found_doc = name
            break
    
    if not found_doc:
        await update.message.reply_text(
            f"❌ *Document non trouvé :* `{doc_name}`",
            parse_mode='Markdown'
        )
        return
    
    processing_msg = await update.message.reply_text(
        f"🎤 *Génération du résumé audio pour :* `{found_doc}`\n"
        "⏳ _En cours..._",
        parse_mode='Markdown'
    )
    
    try:
        content = documents_cache[found_doc]
        words = len(content.split())
        content_preview = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""Fais un résumé ORAL et concis de ce document.

IMPORTANT pour le format audio :
- Parle naturellement, comme si tu racontais à un ami
- Pas de formatage, pas de listes à puces
- Maximum 5-6 phrases fluides
- Commence par "Ce document parle de..."
- Termine par une phrase de conclusion

Document : {found_doc}
Contenu : {content_preview}"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        
        # Générer l'audio
        audio_bytes = await generate_audio(summary)
        
        if audio_bytes:
            await processing_msg.edit_text(
                f"✅ *Résumé audio de :* `{found_doc}`\n\n"
                f"📊 _Document de {words:,} mots_\n\n"
                f"📝 _Transcription :_\n{summary}",
                parse_mode='Markdown'
            )
            
            await update.message.reply_voice(
                voice=audio_bytes,
                caption=f"🎧 *Résumé : {found_doc}*",
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(
                f"❌ *Erreur audio*\n\n📝 *Résumé texte :*\n{summary}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Erreur summary_audio: {e}")
        await processing_msg.edit_text(
            "❌ *Erreur*\n_Utilise `/summary` pour la version texte_",
            parse_mode='Markdown'
        )

# Commande /read (lecture complète d'un document)
async def read_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lire un document entier en audio"""
    if not documents_cache:
        await update.message.reply_text(
            "📂 *Aucun document disponible*",
            parse_mode='Markdown'
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "📖 *Utilisation :* `/read [nom du document]`\n\n"
            "_Lit les premières lignes du document_",
            parse_mode='Markdown'
        )
        return
    
    doc_name = ' '.join(context.args)
    found_doc = None
    for name in documents_cache.keys():
        if doc_name.lower() in name.lower():
            found_doc = name
            break
    
    if not found_doc:
        await update.message.reply_text(
            f"❌ *Document non trouvé :* `{doc_name}`",
            parse_mode='Markdown'
        )
        return
    
    processing_msg = await update.message.reply_text(
        f"📖 *Lecture audio de :* `{found_doc}`\n"
        "⏳ _Préparation..._",
        parse_mode='Markdown'
    )
    
    try:
        content = documents_cache[found_doc]
        # Limiter à 1000 caractères pour la lecture
        content_to_read = content[:1000] if len(content) > 1000 else content
        
        # Ajouter une intro
        reading_text = f"Lecture du document {found_doc}. {content_to_read}"
        
        audio_bytes = await generate_audio(reading_text)
        
        if audio_bytes:
            await processing_msg.edit_text(
                f"✅ *Lecture du début de :* `{found_doc}`\n\n"
                f"📏 _Extrait de {len(content_to_read)} caractères_",
                parse_mode='Markdown'
            )
            
            await update.message.reply_voice(
                voice=audio_bytes,
                caption=f"📖 *{found_doc}*",
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text("❌ *Erreur de lecture*", parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Erreur read: {e}")
        await processing_msg.edit_text("❌ *Erreur*", parse_mode='Markdown')

# Commande /voice pour activer/désactiver la synthèse vocale
async def voice_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activer/désactiver les réponses vocales"""
    if not context.args:
        await update.message.reply_text(
            "🔊 *Utilisation :* `/voice on` ou `/voice off`\n\n"
            "_Active ou désactive les réponses vocales automatiques_",
            parse_mode='Markdown'
        )
        return
    
    mode = context.args[0].lower()
    user_id = update.effective_user.id
    
    if mode == "on":
        context.user_data['voice_enabled'] = True
        await update.message.reply_text(
            "✅ *Réponses vocales activées !*\n\n"
            "🎧 Les commandes `/explain` et `/summary` incluront maintenant de l'audio",
            parse_mode='Markdown'
        )
    elif mode == "off":
        context.user_data['voice_enabled'] = False
        await update.message.reply_text(
            "🔇 *Réponses vocales désactivées*\n\n"
            "_Utilise les commandes_ `_audio` _pour l'audio à la demande_",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Option invalide*\n\n"
            "Utilise `/voice on` ou `/voice off`",
            parse_mode='Markdown'
        )

# Importer les fonctions du bot principal
from bot_railway import (
    sync_github, list_docs, search_in_docs, analyze_docs,
    quiz_command, flashcards_command, explain_command, 
    mindmap_command, answer_question, handle_voice
)

# Version modifiée de summary pour inclure l'audio si activé
async def summary_with_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Résumé avec option vocale"""
    # D'abord faire le résumé texte normal
    from bot_railway import summary_doc
    await summary_doc(update, context)
    
    # Si la voix est activée, ajouter l'audio
    if context.user_data.get('voice_enabled', False) and context.args:
        await summary_audio(update, context)

# Version modifiée d'explain pour inclure l'audio si activé  
async def explain_with_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explication avec option vocale"""
    # D'abord faire l'explication texte
    await explain_command(update, context)
    
    # Si la voix est activée, ajouter l'audio
    if context.user_data.get('voice_enabled', False) and context.args:
        await explain_audio(update, context)

# Fonction principale
def main():
    """Démarrer le bot avec ElevenLabs"""
    logger.info("🚀 Démarrage du bot avec synthèse vocale ElevenLabs...")
    logger.info(f"📚 Repository : {GITHUB_REPO}")
    
    try:
        # Créer l'application
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Handlers de base
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("sync", sync_github))
        app.add_handler(CommandHandler("list", list_docs))
        app.add_handler(CommandHandler("search", search_in_docs))
        app.add_handler(CommandHandler("analyze", analyze_docs))
        
        # Handlers vocaux
        app.add_handler(CommandHandler("explain_audio", explain_audio))
        app.add_handler(CommandHandler("summary_audio", summary_audio))
        app.add_handler(CommandHandler("read", read_document))
        app.add_handler(CommandHandler("voice", voice_toggle))
        
        # Handlers avec option vocale
        app.add_handler(CommandHandler("summary", summary_with_voice))
        app.add_handler(CommandHandler("explain", explain_with_voice))
        
        # Autres handlers
        app.add_handler(CommandHandler("quiz", quiz_command))
        app.add_handler(CommandHandler("flashcards", flashcards_command))
        app.add_handler(CommandHandler("mindmap", mindmap_command))
        
        # Messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        
        # Démarrer
        logger.info("✅ Bot avec synthèse vocale démarré !")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()