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
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
CHATPDF_KEY = os.environ.get("CHATPDF_API_KEY")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ghaf35/mes-cours")

# Vérifier la config
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN manquant !")
    sys.exit(1)

if not CHATPDF_KEY:
    logger.error("❌ CHATPDF_API_KEY manquant ! Le bot a besoin de ChatPDF pour fonctionner.")
    sys.exit(1)

logger.info(f"✅ Configuration OK - Repo: {GITHUB_REPO}")
logger.info("✅ ChatPDF API Key détectée")

# Cache des documents
documents_cache = {}
chatpdf_sources = {}  # Stocke les sourceId ChatPDF

# Fonction de synchronisation automatique au démarrage
async def auto_sync_at_startup():
    """Synchronise automatiquement les documents au démarrage du bot"""
    logger.info("🔄 Synchronisation automatique au démarrage...")
    
    try:
        # Vider le cache
        documents_cache.clear()
        chatpdf_sources.clear()
        
        # Headers pour l'API GitHub
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Récupérer la liste des fichiers
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"❌ Erreur GitHub : {response.status_code}")
            return False
        
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
                            source_id = await upload_to_chatpdf(raw_url, file['name'])
                            if source_id:
                                logger.info(f"✅ {file['name']} uploadé sur ChatPDF")
                    else:
                        # Fichier texte
                        text = file_response.text
                    
                    # Stocker en cache
                    documents_cache[file['name']] = text
                    loaded += 1
                    logger.info(f"✅ Document chargé : {file['name']}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur avec {file['name']}: {e}")
        
        if loaded > 0:
            logger.info(f"✅ Synchronisation automatique terminée : {loaded} documents")
            logger.info(f"📚 Documents disponibles : {list(documents_cache.keys())}")
            if chatpdf_sources:
                logger.info(f"🤖 Documents sur ChatPDF : {list(chatpdf_sources.keys())}")
            return True
        else:
            logger.warning("⚠️ Aucun document trouvé lors de la synchronisation automatique")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur synchronisation automatique : {e}")
        return False

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
        r'explique[\s-]*(?:moi\s+)?(.+)',
        r'c\'est\s+quoi\s+(.+)',
        r'qu\'est[\s-]*ce\s+que\s+(.+)',
        r'cherche\s+(.+?)(?:\s+dans|$)',
        r'trouve\s+(.+?)(?:\s+dans|$)',
        r'sur\s+(.+?)(?:\s+dans|$)',
        r'définition\s+(?:de\s+)?(.+)',
        r'role\s+(?:de\s+)?(.+)',
        r'qu\'est\s+ce\s+qu[\'e]\s+(.+)'
    ]
    
    message_lower = message.lower()
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            concept = match.group(1).strip()
            # Nettoyer le concept
            concept = concept.replace('?', '').replace('.', '').strip()
            # Enlever les mots vides à la fin
            concept = re.sub(r'\s+(dans|sur|avec|pour|par)\s*$', '', concept)
            return concept
    
    # Si aucun pattern ne match, essayer de deviner le concept
    # après des mots clés comme "explique"
    keywords = ['explique', 'définition', 'c\'est quoi', 'qu\'est-ce']
    for keyword in keywords:
        if keyword in message_lower:
            # Prendre tout ce qui suit le mot clé
            index = message_lower.find(keyword) + len(keyword)
            potential_concept = message[index:].strip()
            # Enlever "moi" s'il est au début
            potential_concept = re.sub(r'^[\s-]*moi\s+', '', potential_concept)
            if potential_concept:
                return potential_concept.replace('?', '').replace('.', '').strip()
    
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
            
            # Nettoyer la réponse de ChatPDF si elle contient les marqueurs
            # Note: Il semble que ChatPDF n'ajoute pas ces marqueurs dans sa réponse JSON
            # mais au cas où, on garde le nettoyage
            
            # Supprimer "📊 Réponse basée sur" au début s'il existe
            if content.startswith('📊'):
                lines = content.split('\n')
                if lines and 'Réponse basée sur' in lines[0]:
                    content = '\n'.join(lines[1:]).strip()
            
            # Supprimer "✅ Source : ChatPDF" à la fin s'il existe
            if '✅' in content and 'ChatPDF' in content:
                lines = content.split('\n')
                if lines and '✅' in lines[-1] and 'ChatPDF' in lines[-1]:
                    content = '\n'.join(lines[:-1]).strip()
            
            # Déplacer les références de page (P11, P12, etc.) après le point final
            # Chercher et extraire toutes les références de page dans le texte
            page_refs = re.findall(r'P(\d+)', content)
            if page_refs:
                # Supprimer les références du milieu du texte
                content = re.sub(r'\s*P\d+', '', content)
                # Ajouter un point si nécessaire
                if not content.rstrip().endswith('.'):
                    content = content.rstrip() + '.'
                # Ajouter les références à la ligne avec emoji
                content += '\n\n📄 Page ' + ', '.join(page_refs)
            
            # Si pas de références inline, vérifier si on doit ajouter depuis les métadonnées
            elif 'references' in result and result['references']:
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
    
    # Message différent selon si les documents sont déjà chargés
    if documents_cache:
        message = f"""
🤖 *Salut ! Je suis ton assistant intelligent !*

✅ *Tes documents sont déjà chargés !* ({len(documents_cache)} fichiers)
Je suis prêt à répondre à tes questions 📚

━━━━━━━━━━━━━━━━━━━━━

💬 *Pose-moi directement ta question !*

Exemples :
• "C'est quoi une zone dangereuse ?"
• "Explique-moi les tâches ESS"
• "Quelles sont les règles de sécurité ?"
• "Fais-moi un quiz"
• "Résume TESM.pdf"

━━━━━━━━━━━━━━━━━━━━━

🔄 _Documents synchronisés automatiquement au démarrage_
"""
    else:
        message = """
🤖 *Salut ! Je suis ton assistant intelligent !*

⚠️ *Aucun document chargé pour le moment*

━━━━━━━━━━━━━━━━━━━━━

💡 *Pour commencer :*
Dis-moi "synchronise mes documents" ou tape `/synchroniser`

Je pourrai ensuite répondre à toutes tes questions sur la sécurité ferroviaire !

━━━━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(message, parse_mode='Markdown')

# Commande /synchroniser (garde la compatibilité)
async def sync_github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Synchroniser avec GitHub"""
    logger.info("Synchronisation GitHub demandée")
    
    # Message différent si c'est une resynchronisation
    if documents_cache:
        await update.message.reply_text(
            f"🔄 *Resynchronisation en cours...*\n\n"
            f"📂 Repository : `{GITHUB_REPO}`\n"
            f"📚 Documents actuels : {len(documents_cache)}\n"
            f"⏳ Mise à jour...",
            parse_mode='Markdown'
        )
    else:
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
        # Si pas de concept extrait, utiliser le message complet
        if not concept:
            # Essayer de nettoyer le message
            concept = message.replace("explique-moi", "").replace("explique", "").strip()
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
    
    # Vérifier si le document existe
    if doc_name not in documents_cache:
        await update.message.reply_text(
            f"😅 Je ne trouve pas le document \"{doc_name}\".\n\n"
            "💡 _Tape \"liste\" pour voir les documents disponibles !_",
            parse_mode='Markdown'
        )
        return
    
    # Utiliser ChatPDF
    if doc_name in chatpdf_sources:
        logger.info(f"Utilisation de ChatPDF pour résumer {doc_name}")
        chatpdf_result = await ask_chatpdf(
            chatpdf_sources[doc_name],
            "Fais un résumé concis de ce document en 3-4 points principaux. Sois clair et structuré."
        )
        
        if chatpdf_result:
            formatted_summary = f"📄 *Résumé de {doc_name}*\n\n"
            formatted_summary += chatpdf_result
            
            await update.message.reply_text(formatted_summary, parse_mode='Markdown')
            return
    
    # Si le document n'est pas sur ChatPDF
    await update.message.reply_text(
        f"❌ *Le document \"{doc_name}\" n'est pas disponible sur ChatPDF*\n\n"
        "💡 Essaie de synchroniser à nouveau tes documents.",
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
    
    # Vérifier si le document existe
    if doc_name not in documents_cache:
        await update.message.reply_text(
            f"😅 Je ne trouve pas le document \"{doc_name}\".\n\n"
            "💡 _Tape \"liste\" pour voir les documents disponibles !_",
            parse_mode='Markdown'
        )
        return
    
    # Utiliser ChatPDF
    if doc_name in chatpdf_sources:
        logger.info(f"Analyse ChatPDF pour {doc_name}")
        chatpdf_result = await ask_chatpdf(
            chatpdf_sources[doc_name],
            "Fais une analyse détaillée et structurée de ce document. Inclus : 1) Résumé exécutif 2) Objectifs principaux 3) Points clés détaillés 4) Structure du document 5) Éléments critiques à retenir. Sois très précis et cite des passages importants."
        )
        
        if chatpdf_result:
            formatted_analysis = f"📊 *Analyse détaillée de {doc_name}*\n\n"
            formatted_analysis += chatpdf_result
            
            await update.message.reply_text(
                formatted_analysis,
                parse_mode='Markdown'
            )
            return
    
    # Si le document n'est pas sur ChatPDF
    await update.message.reply_text(
        f"❌ *Le document \"{doc_name}\" n'est pas disponible sur ChatPDF*\n\n"
        "💡 Essaie de synchroniser à nouveau tes documents.",
        parse_mode='Markdown'
    )

async def quiz_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_name: str):
    """Quiz en langage naturel avec vrais quiz Telegram"""
    if not documents_cache:
        await update.message.reply_text(
            "📝 Pas de documents pour faire un quiz !\n"
            "Dis \"synchronise\" d'abord.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"✏️ *Je prépare un quiz interactif{f' sur {doc_name}' if doc_name else ''}...*\n\n"
        "_Les questions vont arriver une par une !_",
        parse_mode='Markdown'
    )
    
    # Si pas de document spécifié, prendre le premier disponible
    if not doc_name and chatpdf_sources:
        doc_name = list(chatpdf_sources.keys())[0]
        logger.info(f"Pas de document spécifié, utilisation de {doc_name}")
    
    # Utiliser ChatPDF
    if doc_name and doc_name in chatpdf_sources:
        logger.info(f"Génération quiz ChatPDF pour {doc_name}")
        
        # Demander à ChatPDF de créer des questions au format structuré
        chatpdf_result = await ask_chatpdf(
            chatpdf_sources[doc_name],
            """Crée EXACTEMENT 3 questions de quiz. NE PAS faire d'introduction ni de conclusion.
            
Utilise UNIQUEMENT ce format pour chaque question (remplace les crochets par le contenu):

QUESTION: [texte de la question]
REPONSE_A: [option A]
REPONSE_B: [option B]
REPONSE_C: [option C]
REPONSE_D: [option D]
CORRECTE: [lettre A, B, C ou D]
EXPLICATION: [explication courte]

[ligne vide entre chaque question]

Exemple:
QUESTION: Qu'est-ce qu'une zone dangereuse ?
REPONSE_A: Un parking
REPONSE_B: Une zone où les agents risquent d'être heurtés
REPONSE_C: Une cafétéria
REPONSE_D: Un bureau
CORRECTE: B
EXPLICATION: Zone où les agents risquent d'être heurtés par une circulation"""
        )
        
        if chatpdf_result:
            # Parser les questions
            questions = []
            current_q = {}
            
            for line in chatpdf_result.split('\n'):
                line = line.strip()
                if line.startswith('QUESTION:'):
                    if current_q:
                        questions.append(current_q)
                    current_q = {'question': line.replace('QUESTION:', '').strip()}
                elif line.startswith('REPONSE_A:'):
                    current_q['A'] = line.replace('REPONSE_A:', '').strip()
                elif line.startswith('REPONSE_B:'):
                    current_q['B'] = line.replace('REPONSE_B:', '').strip()
                elif line.startswith('REPONSE_C:'):
                    current_q['C'] = line.replace('REPONSE_C:', '').strip()
                elif line.startswith('REPONSE_D:'):
                    current_q['D'] = line.replace('REPONSE_D:', '').strip()
                elif line.startswith('CORRECTE:'):
                    current_q['correct'] = line.replace('CORRECTE:', '').strip()
                elif line.startswith('EXPLICATION:'):
                    current_q['explanation'] = line.replace('EXPLICATION:', '').strip()
            
            if current_q:
                questions.append(current_q)
            
            # Envoyer les quiz Telegram
            if questions:
                quiz_sent = False
                for i, q in enumerate(questions[:3]):  # Limiter à 3 questions
                    if all(k in q for k in ['question', 'A', 'B', 'C', 'D', 'correct']):
                        try:
                            # Préparer les options
                            options = [q['A'], q['B'], q['C'], q['D']]
                            correct_index = ord(q['correct'].upper()) - ord('A')
                            
                            # Vérifier que l'index est valide
                            if 0 <= correct_index <= 3:
                                # Envoyer le quiz
                                await update.message.reply_poll(
                                    question=f"❓ Question {i+1}: {q['question']}",
                                    options=options,
                                    type='quiz',
                                    correct_option_id=correct_index,
                                    explanation=q.get('explanation', f"La bonne réponse est {q['correct']}"),
                                    is_anonymous=False,
                                    allows_multiple_answers=False
                                )
                                quiz_sent = True
                                
                                # Petite pause entre les questions
                                await asyncio.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Erreur envoi quiz: {e}")
                
                if quiz_sent:
                    # Message de fin
                    await update.message.reply_text(
                        f"✅ *Quiz terminé !*\n\n"
                        f"C'était un quiz sur *{doc_name}*\n\n"
                        f"_Dis \"nouveau quiz\" pour recommencer !_",
                        parse_mode='Markdown'
                    )
                    return
            
            # Si pas de questions parsées, envoyer le quiz texte classique
            logger.info("Parsing échoué, envoi du quiz en format texte")
            formatted_quiz = f"🎯 *Quiz sur {doc_name}*\n\n"
            formatted_quiz += chatpdf_result
            formatted_quiz += "\n\n_Dis \"nouveau quiz\" pour un autre !_"
            
            await update.message.reply_text(formatted_quiz, parse_mode='Markdown')
            return
    else:
        await update.message.reply_text(
            "❌ *Aucun document disponible sur ChatPDF pour créer un quiz*\n\n"
            "💡 Synchronise tes documents d'abord !",
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
    
    # Vérifier si le document existe
    if doc_name not in documents_cache:
        await update.message.reply_text(
            f"😅 Je ne trouve pas le document \"{doc_name}\".\n\n"
            "💡 _Tape \"liste\" pour voir les documents disponibles !_",
            parse_mode='Markdown'
        )
        return
    
    # Utiliser ChatPDF
    if doc_name in chatpdf_sources:
        logger.info(f"Génération flashcards ChatPDF pour {doc_name}")
        chatpdf_result = await ask_chatpdf(
            chatpdf_sources[doc_name],
            "Crée 5 cartes de révision (flashcards) sur ce document. Pour chaque carte, propose une question pertinente et sa réponse claire. Utilise ce format : **Carte 1** ❓ Question : [Question] ✅ Réponse : [Réponse]. Base-toi sur les points importants du document."
        )
        
        if chatpdf_result:
            formatted_cards = f"🗂️ *Cartes de révision : {doc_name}*\n\n"
            formatted_cards += chatpdf_result
            formatted_cards += "\n\n📝 _Note ces cartes pour réviser !_"
            
            await update.message.reply_text(formatted_cards, parse_mode='Markdown')
            return
    
    # Si le document n'est pas sur ChatPDF
    await update.message.reply_text(
        f"❌ *Le document \"{doc_name}\" n'est pas disponible sur ChatPDF*\n\n"
        "💡 Essaie de synchroniser à nouveau tes documents.",
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
    
    logger.info(f"Explication demandée pour : '{concept}'")
    logger.info(f"ChatPDF disponible : {bool(CHATPDF_KEY)}")
    logger.info(f"Documents sur ChatPDF : {list(chatpdf_sources.keys())}")
    
    await update.message.reply_text(
        f"🎓 *Je t'explique \"{concept}\"...*",
        parse_mode='Markdown'
    )
    
    # TOUJOURS utiliser ChatPDF si disponible, peu importe le concept
    if CHATPDF_KEY and chatpdf_sources:
        # Prendre le premier document disponible (ou chercher le plus pertinent)
        doc_to_use = None
        
        # D'abord essayer de trouver un document pertinent
        for doc_name in chatpdf_sources.keys():
            if doc_name in documents_cache:
                content_lower = documents_cache[doc_name].lower()
                if concept.lower() in content_lower:
                    doc_to_use = doc_name
                    break
        
        # Si pas de document spécifique, prendre le premier (probablement TESM.pdf)
        if not doc_to_use and len(chatpdf_sources) > 0:
            doc_to_use = list(chatpdf_sources.keys())[0]
        
        if doc_to_use:
            logger.info(f"Explication ChatPDF avec {doc_to_use}")
            # Poser la question directement à ChatPDF
            chatpdf_result = await ask_chatpdf(
                chatpdf_sources[doc_to_use],
                f"Qu'est-ce que '{concept}' ? Donne une explication claire et précise basée sur le document."
            )
            
            if chatpdf_result:
                formatted_explanation = f"🎓 *{concept}*\n\n"
                formatted_explanation += chatpdf_result
                
                await update.message.reply_text(formatted_explanation, parse_mode='Markdown')
                return
            
            # Si ChatPDF ne trouve pas, dire clairement que ce n'est pas dans le document
            await update.message.reply_text(
                f"❌ *'{concept}' n'est pas trouvé dans {doc_to_use}*\n\n"
                "💡 Essaie avec d'autres termes ou vérifie l'orthographe.",
                parse_mode='Markdown'
            )
            return
    
    # Si pas de ChatPDF, message d'erreur clair
    await update.message.reply_text(
        "❌ *ChatPDF n'est pas configuré*\n\n"
        "Pour avoir des réponses précises, ajoute CHATPDF_API_KEY sur Railway.",
        parse_mode='Markdown'
    )
    return

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
    
    # Vérifier si le document existe
    if doc_name not in documents_cache:
        await update.message.reply_text(
            f"😅 Je ne trouve pas le document \"{doc_name}\".\n\n"
            "💡 _Tape \"liste\" pour voir les documents disponibles !_",
            parse_mode='Markdown'
        )
        return
    
    # Utiliser ChatPDF
    if doc_name in chatpdf_sources:
        logger.info(f"Génération carte mentale ChatPDF pour {doc_name}")
        chatpdf_result = await ask_chatpdf(
            chatpdf_sources[doc_name],
            "Crée une carte mentale textuelle de ce document. Utilise ce format visuel : 🎯 **[Thème Central]** ├── 📌 **Branche 1** │   ├── • Point 1.1 │   └── • Point 1.2 ├── 📌 **Branche 2** │   └── • Point 2.1 └── 📌 **Branche 3**     └── • Point 3.1. Organise les idées principales de manière hiérarchique."
        )
        
        if chatpdf_result:
            formatted_mindmap = f"🧠 *Carte mentale : {doc_name}*\n\n"
            formatted_mindmap += chatpdf_result
            formatted_mindmap += "\n\n🎨 _Cette carte résume les idées principales !_"
            
            await update.message.reply_text(formatted_mindmap, parse_mode='Markdown')
            return
    
    # Si le document n'est pas sur ChatPDF
    await update.message.reply_text(
        f"❌ *Le document \"{doc_name}\" n'est pas disponible sur ChatPDF*\n\n"
        "💡 Essaie de synchroniser à nouveau tes documents.",
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
        if documents_cache and chatpdf_sources:
            logger.info("Utilisation de ChatPDF pour répondre")
            
            # Chercher le document le plus pertinent
            question_lower = question.lower()
            best_doc = None
            best_score = 0
            
            for doc_name in chatpdf_sources.keys():
                if doc_name in documents_cache:
                    content_lower = documents_cache[doc_name].lower()
                    score = 0
                    for word in question_lower.split():
                        if len(word) > 3:
                            score += content_lower.count(word)
                    
                    if score > best_score:
                        best_score = score
                        best_doc = doc_name
            
            # Si on a trouvé un document pertinent, utiliser ChatPDF
            if best_doc and best_score > 0:
                logger.info(f"Utilisation de ChatPDF avec {best_doc}")
                chatpdf_result = await ask_chatpdf(
                    chatpdf_sources[best_doc],
                    question
                )
                
                if chatpdf_result:
                    # Formater la réponse ChatPDF
                    formatted_response = chatpdf_result
                    
                    await update.message.reply_text(
                        formatted_response,
                        parse_mode='Markdown'
                    )
                    return
            
            # Si pas de résultat pertinent avec un seul doc, essayer avec le premier
            if len(chatpdf_sources) > 0:
                # Prendre le premier document disponible
                first_doc = list(chatpdf_sources.keys())[0]
                logger.info(f"Pas de document spécifique trouvé, utilisation de {first_doc}")
                chatpdf_result = await ask_chatpdf(
                    chatpdf_sources[first_doc],
                    question
                )
                
                if chatpdf_result:
                    # Envoyer directement la réponse de ChatPDF
                    await update.message.reply_text(
                        chatpdf_result,
                        parse_mode='Markdown'
                    )
                    return
            
            # Si toujours pas de réponse
            await update.message.reply_text(
                "❌ *Je n'ai pas trouvé de réponse dans tes documents*\n\n"
                "💡 Essaie de reformuler ta question ou vérifie que tes documents sont bien synchronisés.",
                parse_mode='Markdown'
            )
        else:
            # Pas de documents synchronisés
            await update.message.reply_text(
                "😊 *Je n'ai pas encore accès à tes documents !*\n\n"
                "Pour que je puisse t'aider, dis-moi :\n"
                "• \"synchronise\" ou\n"
                "• \"charge mes documents\"\n\n"
                "Ensuite je pourrai répondre à toutes tes questions ! 💪",
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
    logger.info("🤖 ChatPDF activé - Toutes les réponses utiliseront ChatPDF")
    
    try:
        # Créer l'application
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Synchronisation automatique au démarrage (avec gestion d'erreur)
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sync_result = loop.run_until_complete(auto_sync_at_startup())
            
            if sync_result:
                logger.info("✅ Documents prêts ! Le bot peut répondre aux questions.")
            else:
                logger.warning("⚠️ Synchronisation automatique échouée, utilisez /synchroniser")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la synchronisation automatique : {e}")
            logger.warning("⚠️ Le bot démarre sans documents préchargés")
        
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
        
        # Synchronisation périodique (optionnel - toutes les heures)
        # Désactivé pour l'instant car nécessite une installation supplémentaire
        # Si besoin plus tard, installer avec: pip install "python-telegram-bot[job-queue]"
        logger.info("ℹ️ Synchronisation périodique désactivée (optionnelle)")
        
        # Démarrer
        logger.info("✅ Bot démarré ! Langage naturel activé 🗣️")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()