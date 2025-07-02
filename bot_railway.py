#!/usr/bin/env python3
"""
Bot Telegram optimisé pour Railway
"""

import os
import sys
import logging
import requests
import tempfile
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
🤖 *Salut ! Je suis ton assistant intelligent !*

Je peux lire tes documents sur GitHub et répondre à tes questions 📖

━━━━━━━━━━━━━━━━━━━━━

📚 *Comment ça marche :*
• Mets tes cours sur GitHub
• Lance `/sync` pour les charger
• Pose-moi tes questions !

🎯 *Commandes disponibles :*
• `/sync` → Charger tes documents
• `/list` → Voir les documents
• `/search [texte]` → Rechercher dans les docs
• `/summary [nom]` → Résumé rapide
• `/analyze [nom]` → Analyse complète
• `/help` → Aide et configuration

━━━━━━━━━━━━━━━━━━━━━

💬 *Pose-moi directement ta question !*
"""
    await update.message.reply_text(message, parse_mode='Markdown')

# Commande /help
async def help_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aide pour configurer GitHub"""
    help_text = f"""
📝 *Configuration actuelle*

🔗 *Repository :* `{GITHUB_REPO}`
✅ *Statut :* Bot actif et prêt !

━━━━━━━━━━━━━━━━━━━━━

💡 *Pour changer de repo :*
Mets à jour la variable `GITHUB_REPO` dans Railway

🆘 *Besoin d'aide ?*
• Vérifie que ton repo est public
• Les fichiers doivent être des PDF ou TXT
• Lance `/sync` après avoir ajouté des fichiers

📋 *Autres commandes :*
• `/search [texte]` → Rechercher un mot/phrase
• `/summary [nom]` → Résumé rapide d'un document
• `/analyze [nom]` → Analyse approfondie
• `/list` → Voir tous les documents

💡 _Conseil : Utilise `/summary` pour un aperçu rapide !_
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Commande /sync
async def sync_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Synchroniser avec GitHub"""
    logger.info("Synchronisation GitHub demandée")
    await update.message.reply_text(
        f"🔄 *Synchronisation en cours...*\n\n"
        f"📂 Repository : `{GITHUB_REPO}`\n"
        f"⏳ Recherche des documents...",
        parse_mode='Markdown'
    )
    
    try:
        # Headers pour l'API GitHub
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Récupérer la liste des fichiers
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ *Erreur GitHub*\n\n"
                f"Code : `{response.status_code}`\n"
                f"Vérifie que le repo *{GITHUB_REPO}* existe et est public !",
                parse_mode='Markdown'
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
        
        if loaded > 0:
            await update.message.reply_text(
                f"✅ *Synchronisation terminée !*\n\n"
                f"📚 *{loaded} documents chargés*\n"
                f"🎯 Tu peux maintenant me poser des questions !\n\n"
                f"💡 _Utilise `/list` pour voir les documents_",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ *Aucun document trouvé*\n\n"
                f"Assure-toi d'avoir des fichiers PDF ou TXT dans ton repo GitHub !",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Erreur sync: {e}")
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# Commande /list
async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lister les documents"""
    if not documents_cache:
        await update.message.reply_text(
            "📂 *Aucun document chargé*\n\n"
            "Utilise `/sync` pour charger tes documents depuis GitHub !",
            parse_mode='Markdown'
        )
        return
    
    message = "📚 *Documents disponibles :*\n\n"
    for i, doc_name in enumerate(documents_cache.keys(), 1):
        # Emoji différent selon le type de fichier
        if doc_name.endswith('.pdf'):
            emoji = "📕"
        elif doc_name.endswith('.txt'):
            emoji = "📄"
        elif doc_name.endswith('.md'):
            emoji = "📝"
        else:
            emoji = "📋"
        message += f"{emoji} `{doc_name}`\n"
    
    message += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"✨ *{len(documents_cache)} documents prêts !*\n"
    message += f"💬 _Pose-moi tes questions !_"
    await update.message.reply_text(message, parse_mode='Markdown')

# Commande /search
async def search_in_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rechercher un texte dans les documents"""
    if not context.args:
        await update.message.reply_text(
            "🔍 *Utilisation :* `/search [mot ou phrase]`\n\n"
            "Exemple : `/search photosynthèse`",
            parse_mode='Markdown'
        )
        return
    
    search_term = ' '.join(context.args).lower()
    logger.info(f"Recherche de : {search_term}")
    
    if not documents_cache:
        await update.message.reply_text(
            "📂 *Aucun document chargé*\n\n"
            "Utilise `/sync` d'abord !",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🔍 *Recherche de :* `{search_term}`\n"
        f"⏳ _Analyse en cours..._",
        parse_mode='Markdown'
    )
    
    # Rechercher dans tous les documents
    results = []
    for doc_name, content in documents_cache.items():
        lines = content.split('\n')
        matches = []
        
        for i, line in enumerate(lines):
            if search_term in line.lower():
                # Contexte : ligne avant et après
                start = max(0, i-1)
                end = min(len(lines), i+2)
                context_lines = lines[start:end]
                context_text = '\n'.join(context_lines)
                
                # Limiter la longueur
                if len(context_text) > 200:
                    context_text = context_text[:200] + "..."
                
                matches.append({
                    'line': i + 1,
                    'context': context_text,
                    'exact': line.strip()
                })
        
        if matches:
            results.append({
                'document': doc_name,
                'matches': matches[:3]  # Max 3 par document
            })
    
    # Formater les résultats
    if results:
        message = f"*🔍 Résultats pour* `{search_term}` *:*\n\n"
        
        for result in results:
            emoji = "📕" if result['document'].endswith('.pdf') else "📄"
            message += f"{emoji} *{result['document']}*\n"
            
            for match in result['matches']:
                message += f"   _Ligne {match['line']}:_\n"
                # Mettre en évidence le terme recherché
                highlighted = match['context'].replace(
                    search_term, 
                    f"*{search_term}*"
                )
                message += f"   {highlighted}\n\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        message += f"✅ *{sum(len(r['matches']) for r in results)} occurrences trouvées*"
    else:
        message = (
            f"❌ *Aucun résultat pour* `{search_term}`\n\n"
            f"💡 _Essaie avec d'autres mots-clés_"
        )
    
    # Envoyer par morceaux si trop long
    if len(message) > 4000:
        message = message[:3900] + "\n\n_... résultats tronqués_"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# Commande /analyze
async def analyze_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyser un document spécifique"""
    if not documents_cache:
        await update.message.reply_text(
            "📂 *Aucun document disponible*\n\n"
            "Utilise `/sync` pour charger des documents !",
            parse_mode='Markdown'
        )
        return
    
    # Si pas d'argument, montrer l'usage
    if not context.args:
        message = "📊 *Utilisation :* `/analyze [nom du document]`\n\n"
        message += "*Documents disponibles :*\n"
        for doc_name in documents_cache.keys():
            emoji = "📕" if doc_name.endswith('.pdf') else "📄"
            message += f"{emoji} `{doc_name}`\n"
        message += "\n_Exemple :_ `/analyze document.pdf`"
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    # Récupérer le nom du document
    doc_name = ' '.join(context.args)
    
    # Chercher le document (correspondance exacte ou partielle)
    found_doc = None
    for name in documents_cache.keys():
        if doc_name.lower() in name.lower():
            found_doc = name
            break
    
    if not found_doc:
        await update.message.reply_text(
            f"❌ *Document non trouvé :* `{doc_name}`\n\n"
            f"Utilise `/list` pour voir les documents disponibles",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🤖 *Analyse de :* `{found_doc}`\n\n"
        f"⏳ _Analyse en cours..._",
        parse_mode='Markdown'
    )
    
    try:
        # Récupérer le contenu du document
        content = documents_cache[found_doc]
        words = len(content.split())
        chars = len(content)
        
        # Limiter le contenu pour l'analyse (max 5000 caractères pour Mistral)
        if len(content) > 5000:
            content_preview = content[:5000] + "\n\n[... Document tronqué pour l'analyse ...]"
            logger.info(f"Document tronqué : {len(content)} -> 5000 caractères")
        else:
            content_preview = content
        
        # Demander à l'IA une analyse détaillée
        prompt = f"""Tu dois analyser ce document et produire une analyse structurée.
TRÈS IMPORTANT : Utilise le formatage Markdown Telegram avec *astérisques* pour mettre les titres en gras.

Document à analyser : {found_doc}
Contenu :
{content_preview}

INSTRUCTIONS CRITIQUES DE FORMATAGE :
- TOUS les titres doivent être entre astérisques : *Titre*
- Utilise EXACTEMENT ce format, COPIE-COLLE la structure :

*📊 Résumé exécutif*

(Ton résumé ici en 3-4 phrases)

*🎯 Objectifs et thèmes principaux*

• Objectif principal : (ton texte)
• Thème 1 : (ton texte)
• Thème 2 : (ton texte)
• Thème 3 : (ton texte)

*💡 Points clés et propositions*

• Point clé 1 : (ton texte)
• Point clé 2 : (ton texte)
• Point clé 3 : (ton texte)
• Point clé 4 : (ton texte)
• Point clé 5 : (ton texte)

*🔍 Analyse critique*

• *Forces :* (ton texte)
• *Faiblesses :* (ton texte)
• *Opportunités :* (ton texte)

*📝 Structure du document*

• *Introduction :* (ton texte)
• *Développement :* (ton texte)
• *Conclusion :* (ton texte)

*🎓 Pour aller plus loin*

• (question 1)
• (question 2)
• (suggestion de recherche)

━━━━━━━━━━━━━━━━━━━━━

*📈 Informations*
• *Titre :* {found_doc}
• *Taille :* {words:,} mots
• *Type :* {"PDF" if found_doc.endswith('.pdf') else "Texte"}

RAPPEL : Mets TOUS les titres entre *astérisques* pour le gras !"""
        
        # Appeler l'IA
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        
        # Récupérer l'analyse
        analysis = response.choices[0].message.content
        
        # Si le message est trop long pour Telegram, le découper
        if len(analysis) > 4000:
            # Envoyer la première partie
            await update.message.reply_text(analysis[:4000], parse_mode='Markdown')
            # Envoyer la suite
            await update.message.reply_text(
                analysis[4000:] + "\n\n✅ _Analyse terminée_",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(analysis, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur analyse: {e}")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Document analysé: {found_doc}")
        logger.error(f"Taille du document: {len(content)} caractères")
        
        # Message d'erreur plus détaillé
        error_msg = "❌ *Erreur lors de l'analyse*\n\n"
        
        if "rate_limit" in str(e).lower():
            error_msg += "⏱️ _Limite de requêtes atteinte. Attends 1 minute._"
        elif "token" in str(e).lower():
            error_msg += "📏 _Document trop long. Essaie avec un document plus court._"
        else:
            error_msg += f"🔧 _Erreur technique : {type(e).__name__}_\n"
            error_msg += "_Réessaie dans quelques instants_"
        
        await update.message.reply_text(error_msg, parse_mode='Markdown')

# Commande /summary (version simplifiée de analyze)
async def summary_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Résumer rapidement un document"""
    if not documents_cache:
        await update.message.reply_text(
            "📂 *Aucun document disponible*\n\n"
            "Utilise `/sync` pour charger des documents !",
            parse_mode='Markdown'
        )
        return
    
    # Si pas d'argument, montrer l'usage
    if not context.args:
        message = "📄 *Utilisation :* `/summary [nom du document]`\n\n"
        message += "*Pour un résumé rapide d'un document*\n"
        message += "_Exemple :_ `/summary document.pdf`"
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    # Récupérer le nom du document
    doc_name = ' '.join(context.args)
    
    # Chercher le document
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
    
    await update.message.reply_text(
        f"📄 *Résumé de :* `{found_doc}`\n⏳ _En cours..._",
        parse_mode='Markdown'
    )
    
    try:
        content = documents_cache[found_doc]
        words = len(content.split())
        
        # Prendre seulement le début pour un résumé rapide
        content_preview = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""Fais un résumé CONCIS de ce document en utilisant ce format :

*📄 {found_doc}*

*📌 En bref :*
Résume en 2-3 phrases maximum.

*🎯 Points principaux :*
• Point 1
• Point 2
• Point 3

*💡 À retenir :*
Message clé en une phrase.

Document à résumer :
{content_preview}"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        summary += f"\n\n📊 _Document de {words:,} mots_"
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur résumé: {e}")
        await update.message.reply_text(
            "❌ *Erreur*\n_Essaie `/analyze` pour une analyse complète_",
            parse_mode='Markdown'
        )

# Handler pour les messages vocaux
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gérer les messages vocaux"""
    logger.info("Message vocal reçu")
    
    # Message d'attente
    processing_msg = await update.message.reply_text(
        "🎤 *Message vocal reçu*\n⏳ _Transcription en cours..._",
        parse_mode='Markdown'
    )
    
    try:
        # Télécharger le fichier audio
        voice = update.message.voice
        file_id = voice.file_id
        
        # Obtenir le fichier
        new_file = await context.bot.get_file(file_id)
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp_file:
            # Télécharger le fichier
            await new_file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Lire le fichier audio
        with open(tmp_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Nettoyer le fichier temporaire
        os.unlink(tmp_path)
        
        # Utiliser Mistral pour "transcrire" (en fait, on va demander à l'utilisateur de répéter)
        # Note: Mistral ne fait pas de transcription audio native
        await processing_msg.edit_text(
            "🎯 *Transcription audio*\n\n"
            "⚠️ _La transcription automatique n'est pas encore disponible._\n\n"
            "💡 *Options :*\n"
            "• Écris ta question directement\n"
            "• Utilise la fonction dictée de ton clavier\n"
            "• Active la transcription Telegram (maintenir le micro)",
            parse_mode='Markdown'
        )
        
        # Suggestion d'utiliser la transcription native Telegram
        await update.message.reply_text(
            "💡 *Astuce :*\n\n"
            "Telegram peut transcrire automatiquement !\n"
            "• *Android/iOS :* Maintiens le bouton micro et glisse vers le haut\n"
            "• Tu verras apparaître le texte en temps réel\n"
            "• Relâche pour envoyer le texte transcrit",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur traitement vocal: {e}")
        await processing_msg.edit_text(
            "❌ *Erreur avec le message vocal*\n\n"
            "_Essaie d'écrire ta question directement_",
            parse_mode='Markdown'
        )

# Répondre aux questions
async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répondre en utilisant les documents"""
    question = update.message.text
    logger.info(f"Question reçue : {question[:50]}...")
    
    await update.message.reply_text("🤔 *Je cherche dans tes documents...*", parse_mode='Markdown')
    
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

EXEMPLE de réponse bien formatée :

*📚 Réponse à ta question*

Voici ce que j'ai trouvé dans tes documents :

• Premier point important
• Deuxième point clé
• Troisième élément

*💡 Explication détaillée*

Plus de détails ici avec des exemples...

━━━━━━━━━━━━━━━━━━━━━

*📖 Source :* _document.pdf_

INSTRUCTIONS IMPORTANTES pour le formatage :
1. Réponds en te basant UNIQUEMENT sur les documents fournis
2. Utilise le formatage Markdown de Telegram :
   - *texte* pour le gras (utilise-le pour TOUS les titres)
   - _texte_ pour l'italique
   - `code` pour le code ou les termes techniques
   - Utilise des emojis pertinents (📌, 💡, ✅, 📖, 🎯, 📚, ⚡, 🔍, etc.)
3. Structure ta réponse OBLIGATOIREMENT comme ceci :
   - *🎯 Titre principal* (toujours en gras avec emoji)
   - Contenu avec bullet points • 
   - *📌 Sous-titre* (toujours en gras avec emoji)
   - Plus de contenu
   - Utilise ━━━━━━━━━ pour séparer les sections
4. À la fin, ajoute toujours :
   - *📖 Source :* _(nom du document)_
5. Si l'info n'est pas dans les docs :
   - Commence par : *⚠️ Information non trouvée*
   - Explique que tu ne peux répondre qu'avec les documents fournis"""
            
        else:
            prompt = f"""L'utilisateur demande : {question}

Aucun document n'est chargé. Réponds EXACTEMENT avec ce format :

*⚠️ Aucun document disponible*

Je ne peux pas répondre à ta question car aucun document n'est chargé.

*💡 Que faire ?*
• Utilise la commande `/sync` pour charger tes documents
• Assure-toi d'avoir des fichiers dans ton repo GitHub
• Puis repose ta question !

_Besoin d'aide ? Utilise `/help`_"""
        
        # Demander à Mistral
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        # Envoyer la réponse avec parse_mode Markdown
        await update.message.reply_text(
            response.choices[0].message.content,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur réponse: {e}")
        await update.message.reply_text(
            f"❌ *Une erreur s'est produite*\n\n"
            f"Réessaie dans quelques secondes ou contacte le support.",
            parse_mode='Markdown'
        )

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
        app.add_handler(CommandHandler("search", search_in_docs))
        app.add_handler(CommandHandler("analyze", analyze_docs))
        app.add_handler(CommandHandler("summary", summary_doc))
        
        # Messages texte
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))
        
        # Messages vocaux
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        
        # Démarrer
        logger.info("✅ Bot démarré ! Polling en cours...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()