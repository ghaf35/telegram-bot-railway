import os
import io
import asyncio
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle
import logging

from config import Config

logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self):
        self.config = Config()
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authentification Google Drive"""
        creds = None
        
        # Charger le token s'il existe
        if os.path.exists(self.config.TOKEN_PATH):
            with open(self.config.TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
        
        # Si pas de credentials valides
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.CREDENTIALS_PATH, 
                    self.config.GOOGLE_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Sauvegarder le token
            with open(self.config.TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Authentification Google Drive réussie")
    
    async def list_files(self) -> List[Dict[str, Any]]:
        """Lister les fichiers dans le dossier configuré"""
        try:
            query = f"'{self.config.GOOGLE_DRIVE_FOLDER_ID}' in parents"
            query += " and (mimeType='application/pdf'"
            query += " or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
            query += " or mimeType='text/plain')"
            
            results = await asyncio.to_thread(
                self.service.files().list(
                    q=query,
                    fields="files(id, name, mimeType, modifiedTime)"
                ).execute
            )
            
            files = results.get('files', [])
            logger.info(f"{len(files)} fichiers trouvés dans Google Drive")
            return files
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste des fichiers: {e}")
            raise
    
    async def download_file(self, file_id: str) -> bytes:
        """Télécharger un fichier depuis Google Drive"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = await asyncio.to_thread(downloader.next_chunk)
                if status:
                    logger.debug(f"Téléchargement {int(status.progress() * 100)}%")
            
            file_buffer.seek(0)
            return file_buffer.read()
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du fichier {file_id}: {e}")
            raise
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Récupérer les métadonnées d'un fichier"""
        try:
            file = await asyncio.to_thread(
                self.service.files().get(
                    fileId=file_id,
                    fields="id, name, mimeType, modifiedTime, size"
                ).execute
            )
            return file
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métadonnées: {e}")
            raise