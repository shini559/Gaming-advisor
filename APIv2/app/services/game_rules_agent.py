import logging
from typing import List, Dict, Any
from uuid import UUID

from openai import AsyncAzureOpenAI

from app.config import settings
from app.domain.entities.chat_message import MessageSource
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.services.conversation_history_service import IConversationHistoryService
from app.domain.ports.services.game_rules_agent import (
    IGameRulesAgent,
    AgentRequest,
    AgentResponse, 
    AgentContext
)
from app.domain.ports.services.vector_search_service import (
    IVectorSearchService,
    VectorSearchRequest
)

logger = logging.getLogger(__name__)


class GameRulesAgent(IGameRulesAgent):
    """Agent IA spécialisé dans les règles de jeux de société utilisant RAG multimodal"""
    
    def __init__(
        self,
        vector_search_service: IVectorSearchService,
        message_repository: IChatMessageRepository,
        image_repository: IGameImageRepository,
        conversation_history_service: IConversationHistoryService
    ):
        self.vector_search = vector_search_service
        self.message_repository = message_repository
        self.image_repository = image_repository
        self.conversation_history_service = conversation_history_service
        
        # Client Azure OpenAI pour la génération de réponses
        self._chat_client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_vision_api_version
        )
    
    async def generate_response(self, request: AgentRequest) -> AgentResponse:
        """Génère une réponse à partir d'une question utilisateur"""
        logger.info(f"🚀 Agent démarrage - Question: '{request.user_message}', Game ID: {request.game_id}")
        
        try:
            request.validate()
            logger.info("✅ Validation request OK")
            
            # 1. Construire le contexte avec RAG (approche simplifiée du prototype)
            logger.info("🏗️ Construction contexte RAG...")
            context = await self.build_context(request)
            logger.info(f"📊 Contexte créé - Sources: {len(context.vector_results) if hasattr(context, 'vector_results') else 'unknown'}")
            
            # 2. Générer la réponse avec GPT-4 Vision (l'agent décidera si contexte suffisant)
            logger.info("🤖 Génération réponse GPT-4 Vision...")
            response_content, sources, confidence = await self._generate_with_context(context)
            logger.info(f"✅ Réponse générée - Sources: {len(sources)}, Confidence: {confidence}")
            
            return AgentResponse(
                content=response_content,
                sources=sources,
                confidence=confidence,
                search_method=settings.search_method,
                reasoning=f"Réponse générée avec {len(sources)} source(s)"
            )
            
        except Exception as e:
            logger.error(f"💥 ERREUR AGENT: {str(e)}")
            logger.error(f"💥 Type erreur: {type(e).__name__}")
            import traceback
            logger.error(f"💥 Stack trace: {traceback.format_exc()}")
            
            return AgentResponse(
                content="Je rencontre un problème technique. Peux-tu reformuler ta question ?",
                sources=[],
                confidence=0.0,
                search_method=settings.search_method,
                reasoning=f"Erreur: {str(e)}"
            )
    
    # MÉTHODE SUPPRIMÉE: is_game_rules_question()
    # Adopte l'approche prototype : l'agent gère naturellement le scope 
    # via son prompt système "ONLY USE THE DATA PROVIDED"
    
    async def build_context(self, request: AgentRequest) -> AgentContext:
        """Construit le contexte pour l'agent IA"""
        logger.info(f"🏗️ build_context - Game ID: {request.game_id}, Question: '{request.user_message}'")
        
        # 1. Récupérer l'historique de conversation si demandé
        conversation_history = []
        if request.include_conversation_history:
            logger.info("📜 Récupération historique conversation...")
            try:
                messages = await self.conversation_history_service.get_conversation_history_for_agent(
                    request.conversation_id,
                    limit_messages=settings.agent_max_conversation_history
                )
                logger.info(f"📜 Historique récupéré: {len(messages)} messages")
                
                conversation_history = [
                    f"{'Utilisateur' if msg.is_from_user() else 'Assistant'}: {msg.content}"
                    for msg in messages[-10:]  # Limiter à 10 derniers messages
                ]
            except Exception as e:
                logger.error(f"💥 Erreur historique: {str(e)}")
                raise
        
        # 2. Recherche vectorielle dans les règles du jeu
        logger.info(f"🔍 Recherche vectorielle - Game ID: {request.game_id}")
        logger.info(f"🔍 Config - top_k: {settings.vector_search_top_k}, seuil: {settings.vector_similarity_threshold}")
        
        try:
            search_request = VectorSearchRequest(
                game_id=request.game_id,
                query=request.user_message,
                top_k=settings.vector_search_top_k,
                similarity_threshold=settings.vector_similarity_threshold,
                include_images=True
            )
            logger.info(f"🔍 VectorSearchRequest créé: {search_request}")
            
            search_results = await self.vector_search.search_vectors(search_request)
            logger.info(f"🔍 Recherche terminée - {len(search_results) if search_results else 0} résultats")
            
        except Exception as e:
            logger.error(f"💥 ERREUR RECHERCHE VECTORIELLE: {str(e)}")
            logger.error(f"💥 Type: {type(e).__name__}")
            raise
        
        # 3. Formater les résultats pour l'IA (architecture 3-paires)
        formatted_results = []
        for result in search_results:
            formatted_result = {
                'content': result.extracted_text,  # Contenu sélectionné selon search_method
                'similarity': result.similarity_score,
                'page': result.page_number,
                'has_image': result.has_image(),
                'image_url': result.image_url,
                'image_id': str(result.image_id) if result.image_id else None,
                'search_method': settings.search_method,  # Type de recherche utilisé
                'vector_id': str(result.vector_id)
            }
            formatted_results.append(formatted_result)
        
        return AgentContext(
            game_id=request.game_id,
            conversation_history=conversation_history,
            search_results=formatted_results,
            user_question=request.user_message
        )
    
    async def _generate_with_context(self, context: AgentContext) -> tuple[str, List[MessageSource], float]:
        """Génère une réponse avec le contexte fourni (approche hybride)"""
        
        # 1. Si on utilise la méthode labels, récupérer les images originales
        images_content = []
        if settings.search_method == "labels":
            logger.info("📸 Mode labels actif - récupération des images originales")
            
            # Récupérer les IDs des images trouvées
            image_ids = [r['image_id'] for r in context.search_results if r.get('image_id')]
            unique_image_ids = list(set([UUID(id) for id in image_ids if id]))  # Dédupliquer
            
            logger.info(f"📸 {len(unique_image_ids)} images uniques à récupérer")
            
            # Récupérer les images depuis le repository
            for image_id in unique_image_ids:
                try:
                    image = await self.image_repository.get_by_id(image_id)
                    if image and image.blob_url:
                        # Pour GPT-4 Vision, on a besoin des données base64
                        # Ici on utilise l'URL pour simplifier (Azure blob)
                        images_content.append({
                            "type": "image_url",
                            "image_url": {"url": image.blob_url}
                        })
                        logger.info(f"📸 Image ajoutée: {image.original_filename}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur chargement image {image_id}: {e}")
        
        # 2. Construire le prompt avec contexte
        context_text = self._build_context_prompt(context)
        
        # 3. Préparer les messages selon le mode (architecture 3-paires)
        if images_content and settings.search_method == "labels":
            # Mode hybride labels : métadonnées JSON + images directes
            user_content = [
                {"type": "text", "text": f"""Mode de recherche: LABELS (métadonnées JSON)

Contexte des métadonnées trouvées:
{context_text}

Question de l'utilisateur: {context.user_question}

ANALYSE LES IMAGES FOURNIES pour répondre à cette question. Les métadonnées ci-dessus te guident sur le contenu des images, mais base-toi principalement sur ton analyse visuelle directe des règles."""}
            ]
            user_content.extend(images_content)
            
            messages = [
                {"role": "system", "content": settings.agent_system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            logger.info(f"🤖 Envoi à GPT-4 Vision: {len(images_content)} images + contexte textuel")
        else:
            # Mode classique : OCR ou Description textuelle
            search_type_desc = {
                "ocr": "texte OCR extrait",
                "description": "descriptions visuelles",
                "labels": "métadonnées JSON"
            }.get(settings.search_method, "contenu")
            
            messages = [
                {
                    "role": "system", 
                    "content": settings.agent_system_prompt
                },
                {
                    "role": "user",
                    "content": f"""Mode de recherche: {settings.search_method.upper()} ({search_type_desc})

Contexte des règles du jeu:
{context_text}

Question de l'utilisateur: {context.user_question}

Réponds en te basant uniquement sur le contexte fourni. Si tu ne trouves pas la réponse dans le contexte, dis-le clairement."""
                }
            ]
        
        # 3. Appeler GPT-4
        try:
            response = await self._chat_client.chat.completions.create(
                model=settings.azure_openai_vision_deployment,
                messages=messages,
                temperature=0.1,  # Réponses plus déterministes pour les règles
                max_tokens=1000
            )
            
            response_content = response.choices[0].message.content
            
            # 4. Construire les sources
            sources = []
            for result in context.search_results:
                source = MessageSource.create(
                    vector_id=UUID(result['vector_id']),
                    similarity_score=result['similarity'],
                    content_snippet=result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                    image_id=UUID(result.get('image_id')) if result.get('image_id') else None,
                    image_url=result.get('image_url')
                )
                sources.append(source)
            
            # 5. Calculer la confiance basée sur la similarité des sources
            if len(context.search_results) > 0:
                avg_similarity = sum(r['similarity'] for r in context.search_results) / len(context.search_results)
                confidence = min(1.0, avg_similarity * 1.2)  # Boost léger
            else:
                avg_similarity = 0.0
                confidence = 0.1  # Confiance minimale
            
            return response_content, sources, confidence
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération avec GPT-4: {str(e)}")
            raise
    
    def _build_context_prompt(self, context: AgentContext) -> str:
        """Construit le prompt de contexte pour l'IA (architecture 3-paires)"""
        parts = []
        
        # Historique de conversation
        if context.conversation_history:
            parts.append("=== HISTORIQUE DE LA CONVERSATION ===")
            parts.extend(context.conversation_history[-5:])  # 5 derniers échanges
            parts.append("")
        
        # Résultats de recherche avec information sur le type
        if context.search_results:
            search_method = context.search_results[0].get('search_method', 'unknown') if context.search_results else 'unknown'
            method_name = {
                "ocr": "TEXTE OCR EXTRAIT",
                "description": "DESCRIPTIONS VISUELLES", 
                "labels": "MÉTADONNÉES JSON"
            }.get(search_method, "RÈGLES")
            
            parts.append(f"=== {method_name} PERTINENTES ===")
            for i, result in enumerate(context.search_results, 1):
                parts.append(f"Source {i} (similarité: {result['similarity']:.2f}, type: {search_method}):")
                if result.get('page'):
                    parts.append(f"Page: {result['page']}")
                
                # Afficher le contenu selon le type
                if result['content']:
                    parts.append(result['content'])
                else:
                    parts.append("[Pas de contenu textuel - voir image associée]")
                    
                if result['has_image']:
                    parts.append("[Cette source contient des éléments visuels]")
                parts.append("")
        
        return "\n".join(parts)