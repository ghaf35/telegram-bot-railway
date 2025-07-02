# 🎯 Guide Super Simple pour démarrer ton Bot

## 📱 Étape 1 : Créer ton bot sur Telegram (5 min)

1. **Ouvre Telegram** sur ton téléphone
2. **Cherche** `@BotFather` dans la barre de recherche
3. **Clique dessus** et envoie `/start`
4. **Envoie** `/newbot`
5. **Donne un nom** à ton bot (exemple: "Mon Super Bot IA")
6. **Choisis un username** (doit finir par `bot`, exemple: `mon_super_bot_ia_bot`)
7. **IMPORTANT** : Copie le TOKEN qu'il te donne (ressemble à: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## 🔑 Étape 2 : Obtenir une clé Mistral AI (5 min) - GRATUIT !

1. **Va sur** https://console.mistral.ai/
2. **Crée un compte** (tu peux utiliser Google ou GitHub)
3. **Une fois connecté**, va dans "API Keys" (à gauche)
4. **Clique** "Create new key"
5. **Nomme ta clé** (exemple: "Bot Telegram")
6. **COPIE LA CLÉ** tout de suite (elle commence par `...`)

💡 **Pourquoi Mistral ?**
- C'est GRATUIT pour commencer (pas besoin de carte bancaire)
- C'est une IA française 🇫🇷
- Ça marche super bien pour un bot

## ⚙️ Étape 3 : Configurer le bot

1. **Copie le fichier de config** :
```bash
cp .env.example .env
```

2. **Ouvre `.env`** avec TextEdit (Mac) ou Notepad (Windows)

3. **Remplace les valeurs** :
```
TELEGRAM_BOT_TOKEN=COLLE_TON_TOKEN_TELEGRAM_ICI
MISTRAL_API_KEY=COLLE_TA_CLÉ_MISTRAL_ICI
```

4. **Sauvegarde** le fichier

## 🚀 Étape 4 : Installer et lancer

1. **Ouvre le Terminal**
2. **Tape ces commandes** une par une :

```bash
# Aller dans le dossier
cd telegram-rag-bot

# Créer l'environnement Python
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate  # Sur Mac/Linux
# OU
venv\Scripts\activate  # Sur Windows

# Installer les outils
pip install python-telegram-bot mistralai python-dotenv

# Lancer le bot (version simple)
python bot_simple.py
```

## 💬 Étape 5 : Tester ton bot

1. **Va sur Telegram**
2. **Cherche ton bot** (le username que tu as choisi)
3. **Envoie** `/start`
4. **Pose une question** !

## ❌ Si ça marche pas

### "Module not found"
```bash
pip install python-telegram-bot mistralai python-dotenv
```

### "Invalid token"
- Vérifie que tu as bien copié TOUT le token dans `.env`

### "Mistral error"
- Vérifie ta clé API Mistral
- Vérifie qu'elle commence bien par plusieurs caractères alphanumériques

## 🎉 C'est tout !

Ton bot marche ? Super ! Tu peux maintenant :
- Poser des questions
- Le partager avec tes amis
- L'améliorer petit à petit

Besoin d'aide ? Montre-moi le message d'erreur ! 😊