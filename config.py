import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Google Drive
    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    GOOGLE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    
    # Vector DB Configuration
    VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "faiss")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
    
    # Paths
    VECTOR_DB_PATH = "vector_db"
    DOWNLOADS_PATH = "downloads"
    CREDENTIALS_PATH = "credentials.json"
    TOKEN_PATH = "token.json"