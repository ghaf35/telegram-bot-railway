#!/usr/bin/env python3
"""
Bot Telegram avec langage naturel et intégration ChatPDF
"""

import os
import sys
import logging
import requests
import tempfile
import json
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai import Mistral
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
MISTRAL_KEY = os.environ.get("MISTRAL_API_KEY")
CHATPDF_KEY = os.environ.get("CHATPDF_API_KEY")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ghaf35/mes-cours")

# Vérifier la config
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN manquant !")
    sys.exit(1)

if not MISTRAL_KEY:
    logger.error("❌ MISTRAL_API_KEY manquant !")
    sys.exit(1)

logger.info(f"✅ Configuration OK - Repo: {GITHUB_REPO}")
if CHATPDF_KEY:
    logger.info("✅ ChatPDF API Key détectée")

# Initialiser Mistral
try:
    mistral_client = Mistral(api_key=MISTRAL_KEY)
    logger.info("✅ Mistral initialisé")
except Exception as e:
    logger.error(f"❌ Erreur Mistral: {e}")
    sys.exit(1)

# Cache des documents
documents_cache = {}
chatpdf_sources = {}  # Stocke les sourceId ChatPDF

# Fonction pour détecter l'intention de l'utilisateur
def detect_intent(message: str) -> dict:
    """Détecte ce que l'utilisateur veut faire à partir du langage naturel"""
    message_lower = message.lower()
    
    # Patterns pour détecter les intentions
    patterns = {
        'sync': [r'synchronise', r'charge', r'télécharge', r'met à jour', r'actualise'],
        'list': [r'liste', r'montre', r'affiche', r'voir.*documents?', r'qu.*documents?'],
        'search': [r'cherche', r'trouve', r'recherche', r'où.*(?:est|sont)', r'contient'],
        'summary': [r'résume', r'résumé', r'résumer', r'aperçu', r'synthèse'],
        'analyze': [r'analyse', r'analyser', r'détail', r'approfondi'],
        'quiz': [r'quiz', r'qcm', r'test', r'questionnaire', r'exercice'],
        'flashcards': [r'carte', r'fiche', r'révision', r'flashcard'],
        'explain': [r'explique', r'expliquer', r'c\'est quoi', r'qu\'est-ce', r'comprendre', r'définition'],
        'mindmap': [r'carte mentale', r'mind map', r'schéma', r'diagramme'],
        'help': [r'aide', r'comment', r'utilise', r'guide', r'manuel'],
        'chatpdf': [r'tableau', r'graphique', r'page \d+', r'extrait', r'citation']
    }
    
    # Chercher l'intention
    for intent, patterns_list in patterns.items():
        for pattern in patterns_list:
            if re.search(pattern, message_lower):
                # Extraire le document ou le concept mentionné
                doc_name = extract_document_name(message)
                concept = extract_concept(message)
                
                return {
                    'intent': intent,
                    'document': doc_name,
                    'concept': concept,
                    'original': message
                }
    
    # Si aucune intention claire, c'est une question générale
    return {
        'intent': 'question',
        'document': None,
        'concept': None,
        'original': message
    }

def extract_document_name(message: str) -> str:
    """Extrait le nom du document de la phrase"""
    message_lower = message.lower()
    
    # Chercher dans le cache
    for doc_name in documents_cache.keys():
        doc_lower = doc_name.lower()
        doc_base = doc_lower.replace('.pdf', '').replace('.txt', '')
        
        if doc_lower in message_lower or doc_base in message_lower:
            return doc_name
        
        # Chercher des morceaux du nom
        words = doc_base.split('-')
        if len(words) > 1 and any(word in message_lower for word in words if len(word) > 4):
            return doc_name
    
    # Patterns pour extraire des références
    patterns = [
        r'(?:le|la|du|de la|sur|dans)\s+(.+?)(?:\s|$)',
        r'document\s+(.+?)(?:\s|$)',
        r'fichier\s+(.+?)(?:\s|$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            potential_doc = match.group(1).strip()
            # Chercher une correspondance partielle
            for doc_name in documents_cache.keys():
                if potential_doc in doc_name.lower():
                    return doc_name
    
    return None

def extract_concept(message: str) -> str:
    """Extrait le concept ou sujet à expliquer"""
    patterns = [
        r'explique\s+(?:moi\s+)?(.+)',
        r'c\'est quoi\s+(.+)',
        r'qu\'est-ce que\s+(.+)',
        r'cherche\s+(.+?)(?:\s+dans|$)',
        r'trouve\s+(.+?)(?:\s+dans|$)',
        r'sur\s+(.+?)(?:\s+dans|$)'
    ]
    
    message_lower = message.lower()
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            concept = match.group(1).strip()
            # Nettoyer le concept
            concept = concept.replace('?', '').replace('.', '').strip()
            return concept
    
    return None

# ChatPDF Integration
async def upload_to_chatpdf(pdf_url: str, doc_name: str) -> str:
    """Upload un PDF sur ChatPDF et retourne le sourceId"""
    if not CHATPDF_KEY:
        return None
    
    try:
        headers = {
            'x-api-key': CHATPDF_KEY,
            'Content-Type': 'application/json'
        }
        
        data = {
            'url': pdf_url
        }
        
        response = requests.post(
            'https://api.chatpdf.com/v1/sources/add-url',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            source_id = result['sourceId']
            logger.info(f"PDF uploadé sur ChatPDF: {doc_name} -> {source_id}")
            chatpdf_sources[doc_name] = source_id
            return source_id
        else:
            logger.error(f"Erreur ChatPDF upload: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur upload ChatPDF: {e}")
        return None

async def ask_chatpdf(source_id: str, question: str) -> str:
    """Pose une question à ChatPDF"""
    if not CHATPDF_KEY or not source_id:
        return None
    
    try:
        headers = {
            'x-api-key': CHATPDF_KEY,
            'Content-Type': 'application/json'
        }
        
        data = {
            'sourceId': source_id,
            'messages': [
                {
                    'role': 'user',
                    'content': question
                }
            ],
            'referenceSources': True
        }
        
        response = requests.post(
            'https://api.chatpdf.com/v1/chats/message',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['content']
            
            # Formatter avec les références
            if 'references' in result and result['references']:
                content += "\n\n📄 *Sources :*\n"
                for ref in result['references']:
                    if 'pageNumber' in ref:
                        content += f"• Page {ref['pageNumber']}\n"
            
            return content
        else:
            logger.error(f"Erreur ChatPDF question: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur question ChatPDF: {e}")
        return None

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue"""
    logger.info(f"Commande /start de {update.effective_user.username}")
    message = """
🤖 *Salut ! Je suis ton assistant intelligent !*

Je comprends le langage naturel ! Tu peux me parler normalement 💬

━━━━━━━━━━━━━━━━━━━━━

📚 *Exemples de phrases :*
• "Montre-moi mes documents"
• "Résume le guide de sécurité"
• "Cherche les tâches ESS"
• "Fais-moi un quiz sur la sécurité"
• "Explique-moi les annonces"
• "C'est quoi une tâche de sécurité ?"

━━━━━━━━━━━━━━━━━━━━━

💡 *Pour commencer :*
Dis-moi "synchronise mes documents" ou tape `/synchroniser`

🔤 *Les commandes classiques marchent toujours !*
"""
    await update.message.reply_text(message, parse_mode='Markdown')

# Commande /synchroniser (garde la compatibilité)
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
        # Vider le cache avant de synchroniser
        documents_cache.clear()
        chatpdf_sources.clear()
        logger.info("Cache vidé - rechargement complet")
        
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
                        
                        # Si ChatPDF est disponible, uploader
                        if CHATPDF_KEY:
                            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file['name']}"
                            await upload_to_chatpdf(raw_url, file['name'])
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
            message = f"✅ *Synchronisation terminée !*\n\n"
            message += f"📚 *{loaded} documents chargés*\n"
            if CHATPDF_KEY and chatpdf_sources:
                message += f"🤖 *{len(chatpdf_sources)} documents sur ChatPDF*\n"
            message += f"\n💬 Tu peux maintenant me poser des questions !\n"
            message += f"_Exemple : \"Résume le guide de sécurité\"_"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"⚠️ *Aucun document trouvé*\n\n"
                f"Assure-toi d'avoir des fichiers PDF ou TXT dans ton repo GitHub !",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Erreur sync: {e}")
        await update.message.reply_text(f"❌ Erreur : {str(e)}")

# Handler principal pour le langage naturel
async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Traite les messages en langage naturel"""
    message = update.message.text
    logger.info(f"Message reçu : {message[:50]}...")
    
    # Détecter l'intention
    intent_data = detect_intent(message)
    intent = intent_data['intent']
    doc_name = intent_data['document']
    concept = intent_data['concept']
    
    logger.info(f"Intent détecté : {intent}, Document : {doc_name}, Concept : {concept}")
    
    # Router vers la bonne fonction
    if intent == 'sync':
        await sync_github(update, context)
    
    elif intent == 'list':
        await list_docs_natural(update, context)
    
    elif intent == 'search':
        await search_natural(update, context, concept or message)
    
    elif intent == 'summary':
        await summary_natural(update, context, doc_name)
    
    elif intent == 'analyze':
        await analyze_natural(update, context, doc_name)
    
    elif intent == 'quiz':
        await quiz_natural(update, context, doc_name)
    
    elif intent == 'flashcards':
        await flashcards_natural(update, context, doc_name)
    
    elif intent == 'explain':
        await explain_natural(update, context, concept)
    
    elif intent == 'mindmap':
        await mindmap_natural(update, context, doc_name)
    
    elif intent == 'help':
        await help_natural(update, context)
    
    elif intent == 'chatpdf' and CHATPDF_KEY and doc_name:
        await chatpdf_question(update, context, doc_name, message)
    
    else:
        # Question générale
        await answer_question(update, context)

# Versions naturelles des fonctions
async def list_docs_natural(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Liste les documents en langage naturel"""
    if not documents_cache:
        await update.message.reply_text(
            "😅 Je n'ai pas encore de documents !\n\n"
            "Dis-moi \"synchronise\" pour charger tes documents depuis GitHub.",
            parse_mode='Markdown'
        )
        return
    
    message = "📚 *Voici tes documents :*\n\n"
    for i, doc_name in enumerate(documents_cache.keys(), 1):
        emoji = "📕" if doc_name.endswith('.pdf') else "📄"
        message += f"{i}. {emoji} {doc_name}\n"
    
    message += f"\n✨ *{len(documents_cache)} documents disponibles !*\n"
    message += f"\n💡 _Tu peux me dire \"résume [nom]\" ou poser une question !_"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def search_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, search_term: str):
    """Recherche en langage naturel"""
    if not documents_cache:
        await update.message.reply_text(
            "🔍 Je ne peux pas chercher sans documents !\n"
            "Dis \"synchronise\" d'abord.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🔍 *Je cherche \"{search_term}\"...*",
        parse_mode='Markdown'
    )
    
    # Utiliser la fonction de recherche existante
    # (Code de recherche similaire à search_in_docs mais avec messages naturels)
    results = []
    for doc_name, content in documents_cache.items():
        if search_term.lower() in content.lower():
            # Trouver le contexte
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    context_start = max(0, i-1)
                    context_end = min(len(lines), i+2)
                    context_text = '\n'.join(lines[context_start:context_end])
                    
                    results.append({
                        'document': doc_name,
                        'line': i + 1,
                        'context': context_text[:200] + "..." if len(context_text) > 200 else context_text
                    })
                    break
    
    if results:
        message = f"🎯 *J'ai trouvé \"{search_term}\" dans :*\n\n"
        for result in results[:5]:
            message += f"📄 *{result['document']}*\n"
            message += f"_Ligne {result['line']} :_\n"
            message += f"{result['context']}\n\n"
        
        message += f"✅ *{len(results)} résultats trouvés*"
    else:
        message = f"😕 Je n'ai pas trouvé \"{search_term}\" dans tes documents.\n\n"
        message += "💡 _Essaie avec d'autres mots-clés !_"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def summary_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_name: str):
    """Résumé en langage naturel"""
    if not documents_cache:
        await update.message.reply_text(
            "📚 Pas de documents à résumer !\n"
            "Dis \"synchronise\" d'abord.",
            parse_mode='Markdown'
        )
        return
    
    if not doc_name:
        await update.message.reply_text(
            "🤔 Quel document veux-tu que je résume ?\n\n"
            "_Exemple : \"résume le guide de sécurité\"_",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"📖 *Je résume \"{doc_name}\"...*",
        parse_mode='Markdown'
    )
    
    try:
        content = documents_cache[doc_name]
        words = len(content.split())
        content_preview = content[:3000] if len(content) > 3000 else content
        
        prompt = f"""Fais un résumé CONCIS et CLAIR de ce document.

*📄 {doc_name}*

*📌 En bref :*
Résume en 2-3 phrases maximum l'essentiel du document.

*🎯 Points principaux :*
• Point clé 1
• Point clé 2  
• Point clé 3

*💡 À retenir :*
Le message le plus important en une phrase.

Document :
{content_preview}"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        summary += f"\n\n📊 _Document de {words:,} mots résumé !_"
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur résumé: {e}")
        await update.message.reply_text(
            "😅 Oups, je n'ai pas réussi à résumer ce document.\n"
            "_Vérifie le nom du document !_",
            parse_mode='Markdown'
        )

async def analyze_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_name: str):
    """Analyse en langage naturel"""
    if not documents_cache:
        await update.message.reply_text(
            "📊 Pas de documents à analyser !\n"
            "Dis \"synchronise\" d'abord.",
            parse_mode='Markdown'
        )
        return
    
    if not doc_name:
        await update.message.reply_text(
            "🤔 Quel document veux-tu que j'analyse ?\n\n"
            "_Exemple : \"analyse le guide de sécurité\"_",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🔬 *J'analyse \"{doc_name}\" en détail...*",
        parse_mode='Markdown'
    )
    
    # Utiliser ChatPDF si disponible pour une meilleure analyse
    if CHATPDF_KEY and doc_name in chatpdf_sources:
        chatpdf_result = await ask_chatpdf(
            chatpdf_sources[doc_name],
            "Fais une analyse détaillée de ce document avec les points clés, la structure et les éléments importants."
        )
        
        if chatpdf_result:
            await update.message.reply_text(
                f"📊 *Analyse de {doc_name}*\n\n{chatpdf_result}",
                parse_mode='Markdown'
            )
            return
    
    # Sinon utiliser Mistral
    try:
        content = documents_cache[doc_name]
        content_preview = content[:5000] if len(content) > 5000 else content
        
        # Prompt similaire mais adapté au langage naturel
        prompt = f"""Analyse ce document de manière approfondie et structurée.

Document : {doc_name}

Fais une analyse avec :
- Résumé exécutif
- Objectifs principaux
- Points clés
- Structure du document
- Éléments importants à retenir

Contenu :
{content_preview}"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content
        await update.message.reply_text(analysis, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur analyse: {e}")
        await update.message.reply_text(
            "😅 Oups, je n'ai pas réussi à analyser ce document.",
            parse_mode='Markdown'
        )

async def quiz_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_name: str):
    """Quiz en langage naturel"""
    if not documents_cache:
        await update.message.reply_text(
            "📝 Pas de documents pour faire un quiz !\n"
            "Dis \"synchronise\" d'abord.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"✏️ *Je prépare un quiz{f' sur {doc_name}' if doc_name else ''}...*",
        parse_mode='Markdown'
    )
    
    # Logique similaire à quiz_command mais avec messages naturels
    if doc_name and doc_name in documents_cache:
        content = documents_cache[doc_name][:3000]
        doc_display = doc_name
    else:
        # Quiz général sur tous les documents
        all_content = ""
        for name, content in list(documents_cache.items())[:2]:
            all_content += f"\n{name}:\n{content[:1000]}\n"
        content = all_content
        doc_display = "tous tes documents"
    
    try:
        prompt = f"""Crée un QCM de 5 questions sur ce contenu.
        
Format simple et clair :

*🎯 Quiz sur {doc_display}*

**Question 1 :**
[Question]
A) [Réponse]
B) [Réponse]
C) [Réponse]
D) [Réponse]

(Répète pour 5 questions)

*💡 Réponses :*
1. [Lettre] - [Explication]
(etc...)

Contenu : {content}"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        quiz = response.choices[0].message.content
        quiz += "\n\n_Dis \"nouveau quiz\" pour un autre !_"
        
        await update.message.reply_text(quiz, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur quiz: {e}")
        await update.message.reply_text(
            "😅 Oups, je n'ai pas réussi à créer le quiz.",
            parse_mode='Markdown'
        )

async def flashcards_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_name: str):
    """Flashcards en langage naturel"""
    if not documents_cache:
        await update.message.reply_text(
            "🗂️ Pas de documents pour faire des cartes !\n"
            "Dis \"synchronise\" d'abord.",
            parse_mode='Markdown'
        )
        return
    
    if not doc_name:
        await update.message.reply_text(
            "🤔 Pour quel document veux-tu des cartes de révision ?\n\n"
            "_Exemple : \"fais des cartes sur le guide de sécurité\"_",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🗂️ *Je crée des cartes de révision pour \"{doc_name}\"...*",
        parse_mode='Markdown'
    )
    
    try:
        content = documents_cache[doc_name][:3000]
        
        prompt = f"""Crée 5 cartes de révision (flashcards) sur ce document.

Format simple :

*🗂️ Cartes de révision : {doc_name}*

**Carte 1**
❓ Question : [Question ou concept]
✅ Réponse : [Réponse claire]

(Répète pour 5 cartes)

Document : {content}"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.5
        )
        
        flashcards = response.choices[0].message.content
        flashcards += "\n\n📝 _Note ces cartes pour réviser !_"
        
        await update.message.reply_text(flashcards, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur flashcards: {e}")
        await update.message.reply_text(
            "😅 Oups, je n'ai pas réussi à créer les cartes.",
            parse_mode='Markdown'
        )

async def explain_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, concept: str):
    """Explication en langage naturel"""
    if not concept:
        await update.message.reply_text(
            "🤔 Qu'est-ce que tu veux que je t'explique ?\n\n"
            "_Exemple : \"explique-moi les tâches de sécurité\"_",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🎓 *Je t'explique \"{concept}\"...*",
        parse_mode='Markdown'
    )
    
    # Chercher dans les documents si disponibles
    context_text = ""
    if documents_cache:
        for doc_name, content in documents_cache.items():
            if concept.lower() in content.lower():
                # Extraire le contexte
                index = content.lower().find(concept.lower())
                start = max(0, index - 200)
                end = min(len(content), index + 500)
                context_text += f"D'après {doc_name} : {content[start:end]}\n\n"
                if len(context_text) > 1000:
                    break
    
    try:
        prompt = f"""Explique "{concept}" de manière simple et claire pour un adolescent.

{("Contexte des documents : " + context_text) if context_text else ""}

Format simple :

*🎓 {concept}*

*💡 En simple :*
[Explication en 2-3 phrases faciles]

*📌 Points importants :*
• [Point 1]
• [Point 2]
• [Point 3]

*🎯 Exemple concret :*
[Un exemple de la vie réelle]

*✨ À retenir :*
[L'essentiel en 1 phrase]"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3
        )
        
        explanation = response.choices[0].message.content
        
        await update.message.reply_text(explanation, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur explain: {e}")
        await update.message.reply_text(
            "😅 Oups, je n'ai pas réussi à expliquer ça.",
            parse_mode='Markdown'
        )

async def mindmap_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_name: str):
    """Carte mentale en langage naturel"""
    if not documents_cache:
        await update.message.reply_text(
            "🧠 Pas de documents pour faire une carte mentale !\n"
            "Dis \"synchronise\" d'abord.",
            parse_mode='Markdown'
        )
        return
    
    if not doc_name:
        await update.message.reply_text(
            "🤔 Pour quel document veux-tu une carte mentale ?\n\n"
            "_Exemple : \"fais une carte mentale du guide\"_",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🧠 *Je crée une carte mentale pour \"{doc_name}\"...*",
        parse_mode='Markdown'
    )
    
    try:
        content = documents_cache[doc_name][:2500]
        
        prompt = f"""Crée une carte mentale textuelle de ce document.

Format visuel avec indentation :

*🧠 Carte mentale : {doc_name}*

🎯 **[Thème Central]**
├── 📌 **Branche 1**
│   ├── • Point 1.1
│   ├── • Point 1.2
│   └── • Point 1.3
├── 📌 **Branche 2**
│   ├── • Point 2.1
│   └── • Point 2.2
└── 📌 **Branche 3**
    ├── • Point 3.1
    └── • Point 3.2

Document : {content}"""
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.5
        )
        
        mindmap = response.choices[0].message.content
        mindmap += "\n\n🎨 _Cette carte résume les idées principales !_"
        
        await update.message.reply_text(mindmap, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Erreur mindmap: {e}")
        await update.message.reply_text(
            "😅 Oups, je n'ai pas réussi à créer la carte mentale.",
            parse_mode='Markdown'
        )

async def help_natural(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aide en langage naturel"""
    help_text = """
📖 *Comment m'utiliser ?*

🗣️ *Parle-moi naturellement !*

Tu peux dire des choses comme :
• "Montre mes documents"
• "Résume le guide de sécurité"
• "Cherche tâches ESS"
• "Fais un quiz sur la sécurité"
• "Explique-moi les annonces"
• "C'est quoi une tâche de sécurité ?"
• "Analyse le document MT07915"
• "Carte mentale du guide"

💡 *Je comprends aussi :*
• Les questions directes
• Les demandes en langage naturel
• Les commandes classiques (/aide, /liste, etc.)

🚀 *Pour commencer :*
Dis "synchronise" pour charger tes documents !

🤖 *Avec ChatPDF :*
Je peux extraire des tableaux et données précises des PDF !
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def chatpdf_question(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_name: str, question: str):
    """Pose une question spécifique via ChatPDF"""
    if doc_name not in chatpdf_sources:
        await update.message.reply_text(
            f"😅 Je n'ai pas ce document sur ChatPDF.\n"
            f"Je vais utiliser mes capacités normales !",
            parse_mode='Markdown'
        )
        await answer_question(update, context)
        return
    
    await update.message.reply_text(
        f"🤖 *J'interroge ChatPDF pour une réponse précise...*",
        parse_mode='Markdown'
    )
    
    result = await ask_chatpdf(chatpdf_sources[doc_name], question)
    
    if result:
        await update.message.reply_text(
            f"📊 *Réponse de ChatPDF :*\n\n{result}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "😅 ChatPDF n'a pas pu répondre, j'essaie autrement...",
            parse_mode='Markdown'
        )
        await answer_question(update, context)

# Répondre aux questions (version améliorée)
async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répond aux questions en utilisant les documents"""
    question = update.message.text
    logger.info(f"Question reçue : {question[:50]}...")
    
    # Message sympa pendant la recherche
    thinking_messages = [
        "🤔 *Je réfléchis...*",
        "🔍 *Je cherche dans tes documents...*",
        "📚 *Je consulte tes cours...*",
        "🧠 *J'analyse ta question...*"
    ]
    import random
    await update.message.reply_text(
        random.choice(thinking_messages), 
        parse_mode='Markdown'
    )
    
    try:
        if documents_cache:
            # Recherche intelligente dans les documents
            context_text = ""
            question_lower = question.lower()
            
            # Score de pertinence pour chaque document
            relevant_docs = []
            for doc_name, content in documents_cache.items():
                content_lower = content.lower()
                relevance_score = 0
                
                # Calculer la pertinence
                for word in question_lower.split():
                    if len(word) > 3:
                        relevance_score += content_lower.count(word)
                
                if relevance_score > 0:
                    relevant_docs.append((doc_name, content, relevance_score))
            
            # Trier par pertinence
            relevant_docs.sort(key=lambda x: x[2], reverse=True)
            
            # Prendre les plus pertinents
            for doc_name, content, score in relevant_docs[:3]:
                # Extraire les passages pertinents
                passages = []
                for word in question_lower.split():
                    if len(word) > 3 and word in content_lower:
                        index = content_lower.find(word)
                        start = max(0, index - 300)
                        end = min(len(content), index + 700)
                        passage = content[start:end]
                        if passage not in passages:
                            passages.append(passage)
                
                if passages:
                    context_text += f"\n=== {doc_name} ===\n"
                    context_text += "\n---\n".join(passages[:2])
                    context_text += "\n"
            
            # Si ChatPDF est disponible et qu'on cherche des données précises
            if CHATPDF_KEY and any(word in question_lower for word in ['tableau', 'page', 'chiffre', 'données']):
                for doc_name in relevant_docs[:1]:
                    if doc_name[0] in chatpdf_sources:
                        chatpdf_result = await ask_chatpdf(
                            chatpdf_sources[doc_name[0]], 
                            question
                        )
                        if chatpdf_result:
                            context_text += f"\n=== Données précises de {doc_name[0]} ===\n"
                            context_text += chatpdf_result + "\n"
            
            prompt = f"""Tu es un assistant sympathique qui aide un étudiant.
            
QUESTION : {question}

DOCUMENTS DISPONIBLES :
{context_text if context_text else "Aucun passage spécifique trouvé, utilise le contexte général des documents."}

INSTRUCTIONS :
1. Réponds de manière claire et directe
2. Utilise un ton amical et encourageant
3. Si tu cites un document, mentionne-le
4. Structure bien ta réponse avec des emojis
5. Si l'info n'est pas dans les documents, dis-le gentiment

Format ta réponse avec :
- Des titres en *gras*
- Des emojis pertinents
- Des bullet points si nécessaire
- Un ton sympathique et pédagogique"""
            
        else:
            prompt = f"""L'utilisateur demande : {question}

Réponds gentiment qu'il faut d'abord synchroniser les documents :

😊 *Je n'ai pas encore accès à tes documents !*

Pour que je puisse t'aider, dis-moi :
• "synchronise" ou
• "charge mes documents"

Ensuite je pourrai répondre à toutes tes questions ! 💪"""
        
        # Demander à Mistral
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        
        await update.message.reply_text(
            response.choices[0].message.content,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Erreur réponse: {e}")
        await update.message.reply_text(
            "😅 Oups, j'ai eu un petit souci !\n\n"
            "Réessaie dans quelques secondes 🔄",
            parse_mode='Markdown'
        )

# Garder les handlers de commandes pour la compatibilité
async def aide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /aide"""
    await help_natural(update, context)

async def liste_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /liste"""
    await list_docs_natural(update, context)

# Fonction principale
def main():
    """Démarrer le bot avec langage naturel"""
    logger.info("🚀 Démarrage du bot avec langage naturel...")
    logger.info(f"📚 Repository : {GITHUB_REPO}")
    if CHATPDF_KEY:
        logger.info("🤖 ChatPDF activé")
    
    try:
        # Créer l'application
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Handlers de commandes (compatibilité)
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("aide", aide_command))
        app.add_handler(CommandHandler("help", aide_command))
        app.add_handler(CommandHandler("synchroniser", sync_github))
        app.add_handler(CommandHandler("sync", sync_github))
        app.add_handler(CommandHandler("liste", liste_command))
        app.add_handler(CommandHandler("list", liste_command))
        
        # Handler principal pour le langage naturel
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handle_natural_language
        ))
        
        # Démarrer
        logger.info("✅ Bot démarré ! Langage naturel activé 🗣️")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()