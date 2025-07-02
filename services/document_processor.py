import io
import logging
import asyncio
from typing import Union
import PyPDF2
import pdfplumber
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.text import partition_text

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = {
            'application/pdf': self._process_pdf,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._process_docx,
            'text/plain': self._process_text
        }
    
    async def extract_text(self, content: bytes, filename: str) -> str:
        """Extraire le texte d'un document"""
        mime_type = self._get_mime_type(filename)
        
        if mime_type not in self.supported_formats:
            raise ValueError(f"Format non supporté: {mime_type}")
        
        processor = self.supported_formats[mime_type]
        return await processor(content)
    
    def _get_mime_type(self, filename: str) -> str:
        """Déterminer le type MIME basé sur l'extension"""
        ext = filename.lower().split('.')[-1]
        mime_map = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        return mime_map.get(ext, 'unknown')
    
    async def _process_pdf(self, content: bytes) -> str:
        """Extraire le texte d'un PDF"""
        try:
            # Essayer d'abord avec pdfplumber (meilleur pour les tableaux)
            text = await self._extract_with_pdfplumber(content)
            if text and len(text.strip()) > 100:
                return text
            
            # Si échec, utiliser PyPDF2
            text = await self._extract_with_pypdf2(content)
            if text and len(text.strip()) > 100:
                return text
            
            # En dernier recours, utiliser unstructured
            return await self._extract_with_unstructured_pdf(content)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction PDF: {e}")
            raise
    
    async def _extract_with_pdfplumber(self, content: bytes) -> str:
        """Extraction avec pdfplumber"""
        def extract():
            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        
        return await asyncio.to_thread(extract)
    
    async def _extract_with_pypdf2(self, content: bytes) -> str:
        """Extraction avec PyPDF2"""
        def extract():
            text = ""
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        
        return await asyncio.to_thread(extract)
    
    async def _extract_with_unstructured_pdf(self, content: bytes) -> str:
        """Extraction avec unstructured"""
        def extract():
            elements = partition_pdf(file=io.BytesIO(content))
            return "\n".join([str(el) for el in elements])
        
        return await asyncio.to_thread(extract)
    
    async def _process_docx(self, content: bytes) -> str:
        """Extraire le texte d'un DOCX"""
        def extract():
            elements = partition_docx(file=io.BytesIO(content))
            return "\n".join([str(el) for el in elements])
        
        return await asyncio.to_thread(extract)
    
    async def _process_text(self, content: bytes) -> str:
        """Traiter un fichier texte"""
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # Essayer avec d'autres encodages
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return content.decode(encoding)
                except:
                    continue
            raise ValueError("Impossible de décoder le fichier texte")