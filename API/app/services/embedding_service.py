import os
from typing import List
import asyncio

from langchain_openai import AzureOpenAIEmbeddings

from app.config import settings
from app.services.interfaces import BaseEmbeddingService


class AzureEmbeddingService(BaseEmbeddingService):
    """Service d'embedding utilisant Azure OpenAI"""
    
    def __init__(self):
        self.client = AzureOpenAIEmbeddings(
            api_version=settings.embedding_agent_api_version,
            azure_endpoint=settings.embedding_agent_endpoint,
            api_key=os.getenv("SUBSCRIPTION_KEY"),
            deployment=settings.embedding_agent_deployment
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Génère un embedding pour un texte unique
        
        Args:
            text (str): Texte à embedder
            
        Returns:
            List[float]: Vecteur d'embedding
        """
        try:
            # Nettoyage du texte
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text.strip():
                # Retourner un vecteur vide si le texte est vide
                return []
            
            # Génération de l'embedding
            embedding = await self.client.aembed_query(cleaned_text)
            
            return embedding
            
        except Exception as e:
            print(f"Erreur lors de l'embedding du texte: {str(e)}")
            return []
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Génère des embeddings pour une liste de textes
        
        Args:
            texts (List[str]): Liste des textes à embedder
            
        Returns:
            List[List[float]]: Liste des vecteurs d'embedding
        """
        try:
            # Nettoyage des textes
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # Filtrage des textes vides
            non_empty_texts = [text for text in cleaned_texts if text.strip()]
            
            if not non_empty_texts:
                return []
            
            # Génération des embeddings en batch
            embeddings = await self.client.aembed_documents(non_empty_texts)
            
            return embeddings
            
        except Exception as e:
            print(f"Erreur lors de l'embedding batch: {str(e)}")
            # Fallback: traitement un par un
            return await self._embed_batch_fallback(texts)
    
    async def _embed_batch_fallback(self, texts: List[str]) -> List[List[float]]:
        """Traitement fallback un par un en cas d'échec du batch"""
        embeddings = []
        
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
            
            # Petite pause pour éviter les rate limits
            await asyncio.sleep(0.1)
        
        return embeddings
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte avant embedding
        
        Args:
            text (str): Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return ""
        
        # Suppression des espaces multiples et des retours à la ligne excessifs
        cleaned = " ".join(text.split())
        
        # Limitation de la taille si nécessaire (8191 tokens max pour text-embedding-3-large)
        # Approximation: ~4 caractères par token
        max_chars = 32000
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "..."
        
        return cleaned
    
    def get_embedding_dimension(self) -> int:
        """Retourne la dimension des embeddings du modèle actuel"""
        # text-embedding-3-large produit des embeddings de dimension 3072
        return 3072