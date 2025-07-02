#!/usr/bin/env python3
"""
Script pour configurer l'authentification Google Drive

Instructions:
1. Aller sur https://console.cloud.google.com/
2. Créer un nouveau projet ou sélectionner un projet existant
3. Activer l'API Google Drive
4. Créer des credentials OAuth 2.0 (type: Desktop app)
5. Télécharger le fichier credentials.json
6. Placer le fichier dans le dossier du projet
7. Exécuter ce script
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def setup_google_auth():
    """Configuration de l'authentification Google"""
    print("🔐 Configuration de l'authentification Google Drive")
    
    # Vérifier la présence de credentials.json
    if not os.path.exists('credentials.json'):
        print("\n❌ Fichier credentials.json introuvable!")
        print("\nPour obtenir ce fichier:")
        print("1. Aller sur https://console.cloud.google.com/")
        print("2. Créer un nouveau projet ou sélectionner un projet existant")
        print("3. Activer l'API Google Drive")
        print("4. Aller dans 'APIs & Services' > 'Credentials'")
        print("5. Cliquer sur '+ CREATE CREDENTIALS' > 'OAuth client ID'")
        print("6. Type d'application: 'Desktop app'")
        print("7. Télécharger le fichier JSON")
        print("8. Renommer le fichier en 'credentials.json' et le placer ici")
        return False
    
    # Authentification
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES
    )
    
    print("\n🌐 Ouverture du navigateur pour l'authentification...")
    print("Autorisez l'accès à votre Google Drive")
    
    creds = flow.run_local_server(port=0)
    
    # Sauvegarder le token
    with open('token.json', 'wb') as token:
        pickle.dump(creds, token)
    
    print("\n✅ Authentification réussie!")
    print("Le fichier token.json a été créé")
    
    # Demander l'ID du dossier Google Drive
    print("\n📁 Configuration du dossier Google Drive")
    print("\nPour obtenir l'ID d'un dossier:")
    print("1. Ouvrir Google Drive dans votre navigateur")
    print("2. Naviguer vers le dossier souhaité")
    print("3. L'URL sera comme: https://drive.google.com/drive/folders/FOLDER_ID")
    print("4. Copier le FOLDER_ID")
    
    folder_id = input("\nEntrez l'ID du dossier Google Drive: ").strip()
    
    # Mettre à jour le fichier .env
    env_content = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.readlines()
    
    # Mettre à jour ou ajouter GOOGLE_DRIVE_FOLDER_ID
    updated = False
    for i, line in enumerate(env_content):
        if line.startswith('GOOGLE_DRIVE_FOLDER_ID='):
            env_content[i] = f'GOOGLE_DRIVE_FOLDER_ID={folder_id}\n'
            updated = True
            break
    
    if not updated:
        env_content.append(f'\nGOOGLE_DRIVE_FOLDER_ID={folder_id}\n')
    
    with open('.env', 'w') as f:
        f.writelines(env_content)
    
    print(f"\n✅ Configuration terminée!")
    print(f"Dossier configuré: {folder_id}")
    
    return True

if __name__ == "__main__":
    setup_google_auth()