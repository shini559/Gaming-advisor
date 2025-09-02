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
        """Effectue une recherche vectorielle découplée"""
        logger.info(f"🔍 VectorSearchService.search_vectors DÉCOUPLÉ - Game: {request.game_id}, Query: '{request.query}'")
        
        try:
            request.validate()
            logger.info("✅ VectorSearchRequest validé")
            
            # 1. Générer l'embedding de la requête
            logger.info("🧠 Génération embedding OpenAI...")
            query_embedding = await self.generate_embedding(request.query)
            logger.info(f"✅ Embedding généré - Dimensions: {len(query_embedding) if query_embedding else 'None'}")
            
            # 2. Recherche découplée - SEULEMENT selon vector_search_method pour la similarité
            logger.info(f"🗄️ Recherche découplée - Game ID: {request.game_id}, méthode: {settings.vector_search_method}, limit: {request.top_k}")
            logger.info(f"🔍 DEBUG DÉCOUPLÉ: vector_search_method = '{settings.vector_search_method}'")
            vectors = await self.vector_repository.search_by_embedding_type(
                game_id=request.game_id,
                query_embedding=query_embedding,
                embedding_type=settings.vector_search_method,  # DÉCOUPLÉ de agent_content_fields
                limit=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
            logger.info(f"✅ Recherche DB découplée terminée - {len(vectors)} vecteurs trouvés avec méthode '{settings.vector_search_method}'")
            
            # 3. Construire les résultats avec TOUT le contenu (découplé)
            logger.info(f"📊 Construction résultats découplés - {len(vectors)} vecteurs à traiter")
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
                
                # Construire TOUT le contenu disponible (découplé)
                all_content = {
                    "ocr": vector.ocr_content,
                    "description": vector.description_content,
                    "labels": vector.labels_content
                }
                
                result = VectorSearchResult(
                    vector_id=vector.id,
                    game_id=vector.game_id,
                    image_id=vector.image_id,
                    similarity_score=similarity_score,
                    image_url=image_url,
                    page_number=vector.page_number,
                    all_content=all_content  # TOUT le contenu pour l'agent
                )
                
                results.append(result)
                logger.info(f"✅ Résultat découplé ajouté - Recherche: {settings.vector_search_method}, Score: {similarity_score:.3f}")
                logger.info(f"   Contenu disponible: OCR={bool(vector.ocr_content)}, Desc={bool(vector.description_content)}, Labels={bool(vector.labels_content)}")
            
            # 4. Trier par score de similarité décroissant
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"Recherche vectorielle découplée terminée: {len(results)} résultats pour '{request.query}'")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche vectorielle découplée: {str(e)}")
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