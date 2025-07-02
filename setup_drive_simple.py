#!/usr/bin/env python3
"""
Configuration simple pour Google Drive
"""

import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def setup():
    print("🔐 Configuration de Google Drive\n")
    
    # Vérifier credentials.json
    if not os.path.exists('credentials.json'):
        print("❌ ERREUR : Fichier credentials.json introuvable !")
        print("\n📝 Pour obtenir ce fichier :")
        print("1. Va sur https://console.cloud.google.com/")
        print("2. Crée un projet")
        print("3. Active 'Google Drive API'")
        print("4. Crée des identifiants OAuth (type: Desktop)")
        print("5. Télécharge le JSON")
        print("6. Renomme-le en 'credentials.json'")
        print("7. Mets-le dans ce dossier\n")
        return False
    
    print("✅ Fichier credentials.json trouvé !")
    
    # Authentification
    creds = None
    
    # Charger le token s'il existe
    if os.path.exists('token.pickle'):
        print("📱 Token existant trouvé")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Si pas valide, refaire l'auth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Rafraîchissement du token...")
            creds.refresh(Request())
        else:
            print("\n🌐 Ouverture du navigateur pour l'authentification...")
            print("👉 Connecte-toi avec ton compte Google")
            print("👉 Autorise l'accès à Drive\n")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Sauvegarder le token
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("\n✅ Authentification réussie !")
    
    # Demander l'ID du dossier
    print("\n📁 Configuration du dossier Google Drive")
    print("\nPour trouver l'ID d'un dossier :")
    print("1. Va sur https://drive.google.com")
    print("2. Entre dans le dossier avec tes cours")
    print("3. L'URL sera : https://drive.google.com/drive/folders/XXXXXX")
    print("4. Copie la partie XXXXXX\n")
    
    folder_id = input("📝 Colle l'ID du dossier ici : ").strip()
    
    # Sauvegarder dans .env
    with open('.env', 'a') as f:
        f.write(f"\n# Google Drive\n")
        f.write(f"GOOGLE_DRIVE_FOLDER_ID={folder_id}\n")
    
    print(f"\n✅ Super ! Dossier configuré : {folder_id}")
    print("\n🎉 Configuration terminée !")
    print("Tu peux maintenant lancer le bot avec Google Drive !")
    
    return True

if __name__ == "__main__":
    setup()