# 📚 Guide : Connecter Google Drive à ton Bot

## 🎯 Ce qu'on va faire
Ton bot pourra lire tes PDF et documents sur Google Drive pour répondre à tes questions !

## 📝 Étape 1 : Créer un projet Google Cloud (10 min)

### 1. Va sur Google Cloud Console
👉 https://console.cloud.google.com/

### 2. Crée un nouveau projet
- Clique sur la liste déroulante en haut
- Clique "Nouveau projet"
- Nom : `Bot-Telegram-Drive` (ou ce que tu veux)
- Clique "Créer"

### 3. Active l'API Google Drive
- Dans la barre de recherche, tape "Google Drive API"
- Clique sur "Google Drive API"
- Clique le gros bouton bleu "ACTIVER"

### 4. Crée les identifiants
- Va dans le menu à gauche → "APIs et services" → "Identifiants"
- Clique "+ CRÉER DES IDENTIFIANTS" → "ID client OAuth"
- Si on te demande de configurer l'écran de consentement :
  - Clique "CONFIGURER L'ÉCRAN DE CONSENTEMENT"
  - Choisis "Externe"
  - Remplis juste :
    - Nom de l'app : "Bot Telegram"
    - Email assistance : ton email
    - Email développeur : ton email
  - Clique "Enregistrer et continuer" 3 fois
  - Retourne dans "Identifiants"

### 5. Crée l'ID client OAuth
- Clique "+ CRÉER DES IDENTIFIANTS" → "ID client OAuth"
- Type d'application : **Application de bureau**
- Nom : "Bot Telegram Desktop"
- Clique "CRÉER"

### 6. Télécharge le fichier
- Une fenêtre apparaît avec tes identifiants
- Clique "TÉLÉCHARGER JSON"
- **IMPORTANT** : Renomme le fichier en `credentials.json`
- Mets-le dans le dossier `telegram-rag-bot`

## 🚀 Étape 2 : Autoriser l'accès

Dans le Terminal :
```bash
cd telegram-rag-bot
python setup_google_auth.py
```

Le script va :
1. Ouvrir ton navigateur
2. Te demander de te connecter à Google
3. Te demander d'autoriser l'accès
4. Te demander l'ID du dossier Drive

## 📁 Étape 3 : Trouver l'ID de ton dossier Drive

1. Va sur https://drive.google.com
2. Crée un dossier "Mes Cours" (ou utilise un dossier existant)
3. Entre dans le dossier
4. Regarde l'URL : `https://drive.google.com/drive/folders/ABC123xyz`
5. Copie la partie après `folders/` → C'est l'ID !

## ✅ C'est fait !

Maintenant ton bot peut accéder à tes documents Google Drive !

## 🆘 Problèmes fréquents

**"Fichier credentials.json introuvable"**
- Vérifie que tu as bien téléchargé et renommé le fichier
- Il doit être dans le dossier `telegram-rag-bot`

**"Erreur 403"**
- Vérifie que l'API Google Drive est bien activée
- Retourne sur la console et vérifie

**"Le navigateur ne s'ouvre pas"**
- Copie l'URL affichée dans le Terminal
- Colle-la dans ton navigateur manuellement