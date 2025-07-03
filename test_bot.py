#!/usr/bin/env python3
"""
Script de test pour vérifier que le bot fonctionne sans Mistral
"""

import os
import sys

# Vérifier les variables d'environnement
print("🔍 Vérification de la configuration...")

if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    print("❌ TELEGRAM_BOT_TOKEN manquant !")
    sys.exit(1)
else:
    print("✅ TELEGRAM_BOT_TOKEN trouvé")

if not os.environ.get("CHATPDF_API_KEY"):
    print("❌ CHATPDF_API_KEY manquant !")
    print("   Le bot a besoin de ChatPDF pour fonctionner.")
    sys.exit(1)
else:
    print("✅ CHATPDF_API_KEY trouvé")

# Vérifier que Mistral n'est PAS requis
if os.environ.get("MISTRAL_API_KEY"):
    print("⚠️  MISTRAL_API_KEY trouvé mais n'est plus nécessaire")
else:
    print("✅ Pas de MISTRAL_API_KEY (normal, le bot utilise uniquement ChatPDF)")

print(f"📚 Repository GitHub : {os.environ.get('GITHUB_REPO', 'ghaf35/mes-cours')}")

# Essayer d'importer les modules
print("\n🔍 Vérification des imports...")
try:
    import telegram
    print("✅ python-telegram-bot installé")
except ImportError:
    print("❌ python-telegram-bot manquant !")
    sys.exit(1)

try:
    import mistralai
    print("⚠️  mistralai installé mais n'est plus utilisé")
except ImportError:
    print("✅ mistralai non installé (normal)")

try:
    import PyPDF2
    print("✅ PyPDF2 installé")
except ImportError:
    print("❌ PyPDF2 manquant !")
    sys.exit(1)

try:
    import requests
    print("✅ requests installé")
except ImportError:
    print("❌ requests manquant !")
    sys.exit(1)

print("\n✅ Toutes les vérifications sont passées !")
print("🚀 Le bot est prêt à utiliser uniquement ChatPDF")
print("\n💡 Pour lancer le bot : python bot_natural.py")