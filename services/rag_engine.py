import os
import asyncio
import logging
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS, Chroma
from langchain.schema import Document
import pickle

from config import Config

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.config = Config()
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.config.OPENAI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        self.vector_store = self._load_or_create_vector_store()
    
    def _load_or_create_vector_store(self):
        """Charger ou créer la base vectorielle"""
        os.makedirs(self.config.VECTOR_DB_PATH, exist_ok=True)
        
        if self.config.VECTOR_DB_TYPE == "faiss":
            index_path = os.path.join(self.config.VECTOR_DB_PATH, "faiss_index")
            if os.path.exists(f"{index_path}.pkl"):
                logger.info("Chargement de l'index FAISS existant")
                return FAISS.load_local(
                    index_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                logger.info("Création d'un nouvel index FAISS")
                return None
        
        elif self.config.VECTOR_DB_TYPE == "chroma":
            persist_dir = os.path.join(self.config.VECTOR_DB_PATH, "chroma")
            logger.info("Utilisation de Chroma DB")
            return Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings
            )
    
    async def add_document(self, text: str, source: str, file_id: str):
        """Ajouter un document à l'index"""
        try:
            # Découper le texte en chunks
            chunks = await asyncio.to_thread(
                self.text_splitter.split_text, text
            )
            
            # Créer des documents LangChain
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "source": source,
                        "file_id": file_id,
                        "chunk_index": i
                    }
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Ajouter à la base vectorielle
            if self.vector_store is None and self.config.VECTOR_DB_TYPE == "faiss":
                self.vector_store = await asyncio.to_thread(
                    FAISS.from_documents, documents, self.embeddings
                )
            else:
                await asyncio.to_thread(
                    self.vector_store.add_documents, documents
                )
            
            # Sauvegarder si FAISS
            if self.config.VECTOR_DB_TYPE == "faiss":
                await self._save_faiss_index()
            
            logger.info(f"Document {source} ajouté: {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du document {source}: {e}")
            raise
    
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Rechercher des documents pertinents"""
        if self.vector_store is None:
            return []
        
        try:
            # Recherche par similarité
            results = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                query,
                k=k
            )
            
            # Formater les résultats
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    async def _save_faiss_index(self):
        """Sauvegarder l'index FAISS"""
        if self.config.VECTOR_DB_TYPE == "faiss" and self.vector_store:
            index_path = os.path.join(self.config.VECTOR_DB_PATH, "faiss_index")
            await asyncio.to_thread(
                self.vector_store.save_local, index_path
            )
    
    async def get_document_count(self) -> int:
        """Obtenir le nombre de documents indexés"""
        if self.vector_store is None:
            return 0
        
        try:
            if self.config.VECTOR_DB_TYPE == "faiss":
                return self.vector_store.index.ntotal
            elif self.config.VECTOR_DB_TYPE == "chroma":
                # Pour Chroma, compter les documents uniques
                results = await asyncio.to_thread(
                    self.vector_store._collection.count
                )
                return results
        except:
            return 0
    
    async def clear_index(self):
        """Effacer l'index"""
        if self.config.VECTOR_DB_TYPE == "faiss":
            self.vector_store = None
            index_path = os.path.join(self.config.VECTOR_DB_PATH, "faiss_index")
            for ext in ['.pkl', '.faiss']:
                if os.path.exists(f"{index_path}{ext}"):
                    os.remove(f"{index_path}{ext}")
        elif self.config.VECTOR_DB_TYPE == "chroma":
            await asyncio.to_thread(self.vector_store._collection.delete)
        
        logger.info("Index effacé")