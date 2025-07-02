import logging
import asyncio
from typing import List, Dict, Any
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from config import Config

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.config = Config()
        self._init_llm_client()
    
    def _init_llm_client(self):
        """Initialiser le client LLM selon la configuration"""
        if self.config.LLM_PROVIDER == "openai":
            self.client = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY)
        elif self.config.LLM_PROVIDER == "anthropic":
            self.client = AsyncAnthropic(api_key=self.config.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Provider LLM non supporté: {self.config.LLM_PROVIDER}")
    
    async def generate_answer(self, question: str, relevant_docs: List[Dict[str, Any]]) -> str:
        """Générer une réponse basée sur les documents pertinents"""
        # Construire le contexte
        context = self._build_context(relevant_docs)
        
        # Créer le prompt
        prompt = self._create_prompt(question, context)
        
        # Générer la réponse selon le provider
        if self.config.LLM_PROVIDER == "openai":
            return await self._generate_openai(prompt)
        elif self.config.LLM_PROVIDER == "anthropic":
            return await self._generate_anthropic(prompt)
    
    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """Construire le contexte à partir des documents"""
        context_parts = []
        for i, doc in enumerate(docs):
            source = doc['metadata']['source']
            content = doc['content']
            context_parts.append(f"[Document {i+1} - {source}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Créer le prompt pour le LLM"""
        return f"""Tu es un assistant expert qui répond aux questions en te basant uniquement sur les documents fournis.

Contexte des documents:
{context}

Question: {question}

Instructions:
1. Réponds uniquement en utilisant les informations présentes dans les documents fournis
2. Si l'information n'est pas dans les documents, dis-le clairement
3. Cite les sources (nom du document) quand tu utilises une information
4. Sois précis et concis dans ta réponse
5. Utilise des bullet points si nécessaire pour structurer ta réponse

Réponse:"""
    
    async def _generate_openai(self, prompt: str) -> str:
        """Générer avec OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un assistant expert qui répond aux questions en te basant sur les documents fournis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erreur OpenAI: {e}")
            raise
    
    async def _generate_anthropic(self, prompt: str) -> str:
        """Générer avec Anthropic"""
        try:
            response = await self.client.messages.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Erreur Anthropic: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Tester la connexion au LLM"""
        try:
            test_prompt = "Réponds simplement 'OK' si tu me reçois."
            
            if self.config.LLM_PROVIDER == "openai":
                response = await self.client.chat.completions.create(
                    model=self.config.LLM_MODEL,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10
                )
                return bool(response.choices[0].message.content)
                
            elif self.config.LLM_PROVIDER == "anthropic":
                response = await self.client.messages.create(
                    model=self.config.LLM_MODEL,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10
                )
                return bool(response.content[0].text)
                
        except Exception as e:
            logger.error(f"Erreur test LLM: {e}")
            return False