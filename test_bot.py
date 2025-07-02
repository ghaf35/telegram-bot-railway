#!/usr/bin/env python3
"""
Test simple pour vérifier la connexion
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Test de configuration...")
print(f"✅ Token Telegram : {'OUI' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NON'}")
print(f"✅ Clé Mistral : {'OUI' if os.getenv('MISTRAL_API_KEY') else 'NON'}")
print(f"✅ GitHub Repo : {os.getenv('GITHUB_REPO', 'Non configuré')}")

# Test simple du bot
from telegram import Bot
import asyncio

async def test():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Pas de token Telegram !")
        return
    
    try:
        bot = Bot(token)
        me = await bot.get_me()
        print(f"\n✅ Bot connecté : @{me.username}")
        print(f"🤖 Nom : {me.first_name}")
        print(f"\n👉 Va sur Telegram et cherche : @{me.username}")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        print("\nVérifie ton token dans .env")

asyncio.run(test())