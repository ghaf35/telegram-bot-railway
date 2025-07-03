# 🚀 Changements importants : ChatPDF uniquement

## ✅ Ce qui a changé

Le bot utilise maintenant **exclusivement ChatPDF** pour toutes les réponses. Mistral AI a été complètement retiré.

### Pourquoi ce changement ?

- ChatPDF donne des réponses **précises** basées sur tes documents
- Plus de réponses génériques sur les vélos ou les travailleurs sociaux !
- Les réponses sont directement tirées de tes PDFs (comme TESM.pdf)

## 🔧 Configuration requise

### Variables d'environnement sur Railway :

```
TELEGRAM_BOT_TOKEN=7650521183:AAGOxj1_TByUxk8SbtIHe1IArQgbByKjapQ
CHATPDF_API_KEY=ton_api_key_chatpdf
GITHUB_REPO=ghaf35/mes-cours
```

⚠️ **IMPORTANT** : Tu n'as plus besoin de `MISTRAL_API_KEY` !

## 📝 Comment ça marche maintenant

1. **Synchronise** : Le bot charge tes documents depuis GitHub et les envoie à ChatPDF
2. **Pose ta question** : Exemple "Qu'est-ce qu'une zone dangereuse ?"
3. **Réponse précise** : ChatPDF analyse tes documents et répond avec le contenu exact

## 🎯 Exemples d'utilisation

```
Tu : Qu'est-ce qu'une zone dangereuse ?
Bot : [Réponse précise tirée de TESM.pdf sur les zones dangereuses ferroviaires]

Tu : Explique-moi les tâches ESS
Bot : [Explication détaillée basée sur tes documents]

Tu : Fais-moi un quiz sur la sécurité
Bot : [Quiz généré à partir du contenu réel de tes PDFs]
```

## ⚡ Déploiement sur Railway

1. Assure-toi d'avoir ajouté `CHATPDF_API_KEY` dans les variables Railway
2. Le bot se redéploiera automatiquement
3. Teste avec des questions sur la sécurité ferroviaire

## 🧪 Pour tester en local

```bash
python test_bot.py  # Vérifie la configuration
python bot_natural.py  # Lance le bot
```

## 💡 Bon à savoir

- Si tu obtiens "Je n'ai pas trouvé de réponse", vérifie que tes documents sont bien synchronisés
- ChatPDF analyse le contenu exact de tes PDFs, donc les réponses seront toujours pertinentes
- Plus besoin de reformuler tes questions plusieurs fois !

---

**Le bot comprend maintenant directement le contexte de tes questions sur la sécurité ferroviaire ! 🚂**