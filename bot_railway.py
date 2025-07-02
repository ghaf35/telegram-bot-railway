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
• `/analyze [nom]` → Analyser un document
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
• `/analyze [nom]` → Analyser un document spécifique
• `/list` → Voir tous les documents

_Exemple :_ `/analyze Livre blanc.pdf`
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
        
        # Limiter le contenu pour l'analyse (max 10000 caractères)
        if len(content) > 10000:
            content_preview = content[:10000] + "..."
        else:
            content_preview = content
        
        # Demander à l'IA une analyse détaillée
        prompt = f"""Analyse ce document en détail et fournis une étude complète.

Document : {found_doc}
Contenu :
{content_preview}

Produis une analyse APPROFONDIE avec ce format EXACT :

*📊 Résumé exécutif*

Résumé du document en 3-4 phrases claires et concises.

*🎯 Objectifs et thèmes principaux*

• Objectif principal : explication
• Thème 1 : description détaillée
• Thème 2 : description détaillée
• Thème 3 : description détaillée

*💡 Points clés et propositions*

• Point clé 1 : explication détaillée
• Point clé 2 : explication détaillée
• Point clé 3 : explication détaillée
• Point clé 4 : explication détaillée
• Point clé 5 : explication détaillée

*🔍 Analyse critique*

• Forces : quels sont les points forts ?
• Faiblesses : quelles sont les limites ?
• Opportunités : quelles pistes à explorer ?

*📝 Structure du document*

• Introduction : résumé
• Développement : points principaux
• Conclusion : messages clés

*🎓 Pour aller plus loin*

• Question 1 à approfondir
• Question 2 à explorer
• Recherches complémentaires suggérées

━━━━━━━━━━━━━━━━━━━━━

*📈 Informations*
• Titre : {found_doc}
• Taille : {words:,} mots
• Type : {"PDF" if found_doc.endswith('.pdf') else "Texte"}

IMPORTANT : Sois très précis et détaillé dans ton analyse. Utilise des emojis et du formatage Markdown !"""
        
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
        await update.message.reply_text(
            "❌ *Erreur lors de l'analyse*\n\n"
            "_Réessaie dans quelques instants_",
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