# 🚂 Déployer ton bot sur Railway (GRATUIT)

## 📋 Prérequis
- Compte GitHub (tu l'as déjà)
- Compte Railway (on va le créer)

## 🚀 Étapes simples

### 1️⃣ Mettre le code sur GitHub

```bash
# Dans le dossier telegram-rag-bot
git add .
git commit -m "Mon bot Telegram"

# Créer un nouveau repo sur GitHub
# Va sur https://github.com/new
# Nom: telegram-bot-railway
# Laisse en Public
# Clique "Create repository"

# Connecter et pousser
git remote add origin https://github.com/ghaf35/telegram-bot-railway.git
git branch -M main
git push -u origin main
```

### 2️⃣ Déployer sur Railway

1. **Va sur** https://railway.app
2. **Clique** "Start a New Project"
3. **Connecte-toi** avec GitHub
4. **Clique** "Deploy from GitHub repo"
5. **Choisis** ton repo `telegram-bot-railway`
6. **Railway détecte** automatiquement que c'est du Python !

### 3️⃣ Configurer les variables

Dans Railway, va dans l'onglet "Variables" et ajoute :

```
TELEGRAM_BOT_TOKEN = (ton token)
MISTRAL_API_KEY = (ta clé)
GITHUB_REPO = ghaf35/mes-cours
```

### 4️⃣ C'est fait !

Railway va :
- ✅ Installer les dépendances
- ✅ Lancer ton bot
- ✅ Le garder actif 24/7
- ✅ Redémarrer si crash

## 📊 Limites gratuites Railway

- 500 heures/mois (largement assez)
- $5 de crédit gratuit
- Parfait pour un bot Telegram !

## 🔧 Commandes utiles

### Voir les logs
Dans Railway, clique sur ton déploiement → "View Logs"

### Redémarrer
Settings → Restart

### Mettre à jour
```bash
git add .
git commit -m "Update"
git push
```
Railway redéploie automatiquement !

## 🆘 Problèmes ?

**Le bot ne démarre pas**
- Vérifie les logs dans Railway
- Vérifie tes variables d'environnement

**Erreur de module**
- Vérifie requirements.txt
- Tous les modules doivent y être

## 🎉 Avantages Railway

- Gratuit pour commencer
- Déploiement automatique
- HTTPS inclus
- Logs en temps réel
- Super simple !