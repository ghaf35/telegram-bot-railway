#!/usr/bin/env python3
"""
Extension vocale avec OpenAI Whisper pour transcription
"""

import os
import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes
from openai import OpenAI
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Pour utiliser cette version, ajoute OPENAI_API_KEY dans Railway
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

async def handle_voice_with_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gérer les messages vocaux avec transcription Whisper"""
    if not OPENAI_KEY:
        await update.message.reply_text(
            "🎤 *Fonction vocale*\n\n"
            "Pour activer la transcription, ajoute `OPENAI_API_KEY` dans Railway.\n\n"
            "En attendant, utilise la transcription native Telegram :\n"
            "• Maintiens le micro\n"
            "• Glisse vers le haut\n"
            "• Le texte apparaît automatiquement !",
            parse_mode='Markdown'
        )
        return
    
    logger.info("Message vocal reçu - Transcription Whisper")
    
    # Message d'attente
    processing_msg = await update.message.reply_text(
        "🎤 *Transcription en cours...*",
        parse_mode='Markdown'
    )
    
    try:
        # Initialiser OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        
        # Télécharger le fichier audio
        voice = update.message.voice
        file_id = voice.file_id
        
        # Obtenir le fichier
        new_file = await context.bot.get_file(file_id)
        
        # Créer des fichiers temporaires
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp_ogg:
            await new_file.download_to_drive(tmp_ogg.name)
            ogg_path = tmp_ogg.name
        
        # Convertir en MP3 (Whisper préfère MP3)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_mp3:
            mp3_path = tmp_mp3.name
        
        # Conversion avec pydub
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(mp3_path, format="mp3")
        
        # Transcrire avec Whisper
        with open(mp3_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="fr"  # Français par défaut
            )
        
        # Nettoyer les fichiers
        os.unlink(ogg_path)
        os.unlink(mp3_path)
        
        # Récupérer le texte transcrit
        text = transcript.text.strip()
        
        if text:
            # Supprimer le message d'attente
            await processing_msg.delete()
            
            # Afficher la transcription
            await update.message.reply_text(
                f"🎤 *Transcription :*\n_{text}_",
                parse_mode='Markdown'
            )
            
            # Traiter comme une question normale
            # (Appeler la fonction answer_question avec le texte)
            update.message.text = text
            await answer_question(update, context)
        else:
            await processing_msg.edit_text(
                "❌ *Aucun texte détecté*\n\n"
                "_Réessaie en parlant plus clairement_",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Erreur transcription Whisper: {e}")
        await processing_msg.edit_text(
            "❌ *Erreur de transcription*\n\n"
            "💡 _Utilise plutôt la transcription native Telegram :_\n"
            "• Maintiens le micro et glisse vers le haut",
            parse_mode='Markdown'
        )

# Note: Pour activer cette version :
# 1. Ajoute OPENAI_API_KEY dans Railway
# 2. Ajoute ces dépendances dans requirements.txt :
#    - openai
#    - pydub
#    - ffmpeg-python
# 3. Remplace handle_voice par handle_voice_with_whisper dans le handler