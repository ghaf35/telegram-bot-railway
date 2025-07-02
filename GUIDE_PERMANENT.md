# 🤖 Faire tourner ton bot 24/7

## Option 1 : Screen (Le plus simple) ⭐

### Lancer le bot :
```bash
# Créer une nouvelle session
screen -S bot

# Dans la session, lancer le bot
source venv/bin/activate
python bot_github.py

# Détacher avec Ctrl+A puis D
```

### Gérer le bot :
```bash
# Voir les sessions
screen -ls

# Revenir au bot
screen -r bot

# Tuer la session
screen -X -S bot quit
```

## Option 2 : PM2 (Plus pro)

### Installer PM2 :
```bash
npm install -g pm2
```

### Lancer le bot :
```bash
# Démarrer
pm2 start ecosystem.config.js

# Voir les logs
pm2 logs telegram-bot

# Arrêter
pm2 stop telegram-bot

# Redémarrer
pm2 restart telegram-bot

# Supprimer
pm2 delete telegram-bot
```

### Démarrage automatique :
```bash
# Sauvegarder la config
pm2 save

# Activer au démarrage
pm2 startup
# Suivre les instructions affichées
```

## Option 3 : Service système (Pro)

### Créer le service :
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Contenu :
```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=ton-username
WorkingDirectory=/Users/ghaf/telegram-rag-bot
ExecStart=/Users/ghaf/telegram-rag-bot/venv/bin/python /Users/ghaf/telegram-rag-bot/bot_github.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Activer :
```bash
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## 🎯 Quelle option choisir ?

- **Débutant** → Screen (2 min)
- **Intermédiaire** → PM2 (5 min)
- **Pro** → Service système (10 min)

## 💡 Astuce Cloud (Gratuit)

Pour un bot vraiment 24/7, utilise :
- **Replit** : https://replit.com (gratuit)
- **Railway** : https://railway.app (gratuit)
- **Render** : https://render.com (gratuit)

Upload ton code et c'est parti !