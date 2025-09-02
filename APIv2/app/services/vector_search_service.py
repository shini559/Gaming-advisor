import logging
import math
from typing import List, Optional
from uuid import UUID

from openai import AsyncAzureOpenAI

from app.config import settings
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.services.vector_search_service import (
    IVectorSearchService, 
    VectorSearchRequest, 
    VectorSearchResult
)

logger = logging.getLogger(__name__)


class VectorSearchService(IVectorSearchService):
    """Implémentation du service de recherche vectorielle utilisant Azure OpenAI"""
    
    def __init__(
        self,
        vector_repository: IGameVectorRepository,
        image_repository: IGameImageRepository
    ):
        self.vector_repository = vector_repository
        self.image_repository = image_repository
        
        # Client Azure OpenAI pour les embeddings
        self._embedding_client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_embedding_api_version
        )
    
    async def search_vectors(self, request: VectorSearchRequest) -> List[VectorSearchResult]:
        """Effectue une recherche vectorielle dans les documents d'un jeu spécifique"""
        logger.info(f"🔍 VectorSearchService.search_vectors - Game: {request.game_id}, Query: '{request.query}'")
        
        try:
            request.validate()
            logger.info("✅ VectorSearchRequest validé")
            
            # 1. Générer l'embedding de la requête
            logger.info("🧠 Génération embedding OpenAI...")
            query_embedding = await self.generate_embedding(request.query)
            logger.info(f"✅ Embedding généré - Dimensions: {len(query_embedding) if query_embedding else 'None'}")
            
            # 2. Rechercher les vecteurs similaires selon la méthode configurée (architecture 3-paires)
            logger.info(f"🗄️ Recherche en base - Game ID: {request.game_id}, méthode: {settings.search_method}, limit: {request.top_k}")
            logger.info(f"🔍 DEBUG: settings.search_method = '{settings.search_method}'")
            vectors = await self.vector_repository.search_by_vector_type(
                game_id=request.game_id,
                query_embedding=query_embedding,
                search_type=settings.search_method,
                limit=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
            logger.info(f"✅ Recherche DB terminée - {len(vectors)} vecteurs trouvés avec méthode '{settings.search_method}'")
            
            # 3. Construire les résultats avec architecture 3-paires
            logger.info(f"📊 Construction résultats - {len(vectors)} vecteurs à traiter")
            results = []
            for vector in vectors:
                # Utiliser le score calculé par PostgreSQL
                similarity_score = vector.similarity_score or 0.0
                logger.info(f"🎯 Vecteur {vector.id} - Score: {similarity_score:.3f}")
                
                # Récupérer les infos de l'image si elle existe
                image_url = None
                if vector.image_id and request.include_images:
                    try:
                        image = await self.image_repository.get_by_id(vector.image_id)
                        if image:
                            image_url = image.blob_url
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur récupération image {vector.image_id}: {e}")
                
                # Sélectionner le contenu approprié selon le type de recherche
                content_text = vector.get_content_for_search_type(settings.search_method) or ""
                
                result = VectorSearchResult(
                    vector_id=vector.id,
                    game_id=vector.game_id,
                    image_id=vector.image_id,
                    similarity_score=similarity_score,
                    extracted_text=content_text,  # Contenu approprié selon le type
                    image_url=image_url,
                    page_number=vector.page_number
                )
                
                # PostgreSQL a déjà filtré par seuil, tous les résultats sont pertinents
                results.append(result)
                logger.info(f"✅ Résultat ajouté - Type: {settings.search_method}, Score: {similarity_score:.3f}, Texte: {content_text[:50]}...")
            
            # 4. Trier par score de similarité décroissant
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"Recherche vectorielle terminée: {len(results)} résultats pour '{request.query}'")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche vectorielle: {str(e)}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding pour un texte donné"""
        try:
            if not text.strip():
                raise ValueError("Le texte ne peut pas être vide")
            
            response = await self._embedding_client.embeddings.create(
                model=settings.azure_openai_embedding_deployment,
                input=text.strip(),
                dimensions=settings.azure_openai_embedding_dimensions
            )
            
            embedding = response.data[0].embedding
            
            if len(embedding) != settings.azure_openai_embedding_dimensions:
                raise ValueError(f"Taille d'embedding incorrecte: {len(embedding)} vs {settings.azure_openai_embedding_dimensions}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embedding: {str(e)}")
            raise
    
    async def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcule la similarité cosine entre deux embeddings"""
        try:
            if len(embedding1) != len(embedding2):
                raise ValueError("Les embeddings doivent avoir la même taille")
            
            # Produit scalaire
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            
            # Normes
            norm1 = math.sqrt(sum(a * a for a in embedding1))
            norm2 = math.sqrt(sum(b * b for b in embedding2))
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Similarité cosine
            similarity = dot_product / (norm1 * norm2)
            
            # S'assurer que le résultat est entre 0 et 1
            return max(0.0, min(1.0, (similarity + 1.0) / 2.0))
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de similarité: {str(e)}")
            raise