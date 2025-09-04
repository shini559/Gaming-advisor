import json
import logging
from typing import List, Dict, Any, Union
from uuid import UUID

from openai import AsyncAzureOpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionMessageParam
)

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
            
            # Créer un JSON complet avec toutes les valeurs de configuration
            search_method_config = {
                "search_method": settings.vector_search_method,
                "send_images": settings.agent_send_images,
                "content_fields": settings.agent_content_fields
            }
            
            return AgentResponse(
                content=response_content,
                sources=sources,
                confidence=confidence,
                search_method=json.dumps(search_method_config),
                reasoning=f"Réponse générée avec {len(sources)} source(s) - Recherche: {settings.vector_search_method}, Contenu: {settings.agent_content_fields}, Images: {settings.agent_send_images}"
            )
            
        except Exception as e:
            logger.error(f"💥 ERREUR AGENT: {str(e)}")
            logger.error(f"💥 Type erreur: {type(e).__name__}")
            import traceback
            logger.error(f"💥 Stack trace: {traceback.format_exc()}")
            
            # Créer un JSON complet même en cas d'erreur
            search_method_config = {
                "search_method": settings.vector_search_method,
                "send_images": settings.agent_send_images,
                "content_fields": settings.agent_content_fields
            }
            
            return AgentResponse(
                content="Je rencontre un problème technique. Peux-tu reformuler ta question ?",
                sources=[],
                confidence=0.0,
                search_method=json.dumps(search_method_config),
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
        
        # 3. Formater les résultats pour l'IA (architecture découplée)
        formatted_results = []
        for result in search_results:
            formatted_result = {
                'all_content': result.all_content,  # TOUT le contenu découplé
                'similarity': result.similarity_score,
                'page': result.page_number,
                'has_image': result.has_image(),
                'image_url': result.image_url,
                'image_id': str(result.image_id) if result.image_id else None,
                'vector_id': str(result.vector_id)
            }
            formatted_results.append(formatted_result)
        
        return AgentContext(
            game_id=request.game_id,
            conversation_history=conversation_history,
            search_results=formatted_results,
            user_question=request.user_message,
            # === NOUVELLES INFORMATIONS DÉCOUPLÉES ===
            should_send_images=settings.agent_send_images,
            content_fields=settings.agent_content_fields,
            search_method_used=settings.vector_search_method
        )
    
    async def _generate_with_context(self, context: AgentContext) -> tuple[str, List[MessageSource], float]:
        """Génère une réponse avec le contexte fourni - VERSION DÉCOUPLÉE"""
        
        # 1. IMAGES - découplé de la méthode de recherche
        images_content = []
        if context.should_send_images:
            logger.info("📸 Mode images DÉCOUPLÉ actif - récupération des images originales")
            
            # Récupérer les IDs des images trouvées
            image_ids = [r['image_id'] for r in context.search_results if r.get('image_id')]
            unique_image_ids = list(set([UUID(id) for id in image_ids if id]))  # Dédupliquer
            
            logger.info(f"📸 {len(unique_image_ids)} images uniques à récupérer")
            
            # Récupérer les images depuis le repository
            for image_id in unique_image_ids:
                try:
                    image = await self.image_repository.get_by_id(image_id)
                    if image and image.blob_url:
                        images_content.append({
                            "type": "image_url",
                            "image_url": {"url": image.blob_url}
                        })
                        logger.info(f"📸 Image ajoutée: {image.original_filename}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur chargement image {image_id}: {e}")
        
        # 2. CONTENU TEXTUEL - découplé avec sélection multiple
        context_text = self._build_context_from_fields(context)
        
        # 3. PRÉPARATION MESSAGES - logique simplifiée et découplée
        messages: List[ChatCompletionMessageParam] = []
        
        if images_content:
            # Mode multimodal : contenu sélectionné + images
            user_content = [
                {"type": "text", "text": f"""Configuration découplée:
- Recherche de similarité: {context.search_method_used}
- Contenu textuel: {', '.join(context.content_fields)}
- Envoi d'images: activé

Contexte trouvé dans les règles:
{context_text}

Question de l'utilisateur: {context.user_question}

ANALYSE les images fournies et utilise le contexte textuel pour répondre à cette question."""}
            ]
            user_content.extend(images_content)
            
            system_message: ChatCompletionSystemMessageParam = {
                "role": "system", 
                "content": settings.agent_system_prompt
            }
            user_message: ChatCompletionUserMessageParam = {
                "role": "user", 
                "content": user_content
            }
            messages = [system_message, user_message]
            
            logger.info(f"🤖 Mode multimodal DÉCOUPLÉ: {len(images_content)} images + champs {context.content_fields}")
        else:
            # Mode textuel : contenu sélectionné uniquement
            content_desc = f"champs textuels: {', '.join(context.content_fields)}"
            
            system_message: ChatCompletionSystemMessageParam = {
                "role": "system", 
                "content": settings.agent_system_prompt
            }
            user_message: ChatCompletionUserMessageParam = {
                "role": "user",
                "content": f"""Configuration découplée:
- Recherche de similarité: {context.search_method_used}
- Contenu textuel: {', '.join(context.content_fields)}
- Envoi d'images: désactivé

Contexte trouvé dans les règles:
{context_text}

Question de l'utilisateur: {context.user_question}

Réponds en te basant uniquement sur le contexte fourni. Si tu ne trouves pas la réponse dans le contexte, dis-le clairement."""
            }
            messages = [system_message, user_message]
            
            logger.info(f"🤖 Mode textuel DÉCOUPLÉ: recherche {context.search_method_used}, {content_desc}")
        
        # 3. Appeler GPT-4
        try:
            response = await self._chat_client.chat.completions.create(
                model=settings.azure_openai_vision_deployment,
                messages=messages,
                temperature=0.1,  # Réponses plus déterministes pour les règles
                max_tokens=1000
            )
            
            response_content = response.choices[0].message.content
            
            # 4. Construire les sources (découplé)
            sources = []
            for result in context.search_results:
                # Utiliser le contenu des champs sélectionnés pour le snippet
                from app.domain.ports.services.vector_search_service import VectorSearchResult
                dummy_result = VectorSearchResult(
                    vector_id=UUID(result['vector_id']),
                    game_id=context.game_id,
                    image_id=UUID(result.get('image_id')) if result.get('image_id') else None,
                    similarity_score=result['similarity'],
                    image_url=result.get('image_url'),
                    page_number=result.get('page'),
                    all_content=result['all_content']
                )
                
                content_snippet = dummy_result.get_content_for_fields(context.content_fields)
                snippet_preview = content_snippet[:200] + "..." if len(content_snippet) > 200 else content_snippet
                
                source = MessageSource.create(
                    vector_id=UUID(result['vector_id']),
                    similarity_score=result['similarity'],
                    content_snippet=snippet_preview,
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
    
    def _build_context_from_fields(self, context: AgentContext) -> str:
        """Construit le contexte selon les champs demandés - VERSION DÉCOUPLÉE"""
        parts = []
        
        # Historique de conversation
        if context.conversation_history:
            parts.append("=== HISTORIQUE DE LA CONVERSATION ===")
            parts.extend(context.conversation_history[-5:])  # 5 derniers échanges
            parts.append("")
        
        # Résultats de recherche avec contenu des champs sélectionnés
        if context.search_results:
            content_fields_desc = ', '.join(context.content_fields)
            parts.append(f"=== RÈGLES TROUVÉES (champs: {content_fields_desc}) ===")
            
            for i, result in enumerate(context.search_results, 1):
                parts.append(f"Source {i} (similarité: {result['similarity']:.2f}, recherche: {context.search_method_used}):")
                if result.get('page'):
                    parts.append(f"Page: {result['page']}")
                
                # Construire le contenu à partir des champs sélectionnés
                from app.domain.ports.services.vector_search_service import VectorSearchResult
                dummy_result = VectorSearchResult(
                    vector_id=UUID(result['vector_id']),
                    game_id=context.game_id,
                    image_id=UUID(result.get('image_id')) if result.get('image_id') else None,
                    similarity_score=result['similarity'],
                    image_url=result.get('image_url'),
                    page_number=result.get('page'),
                    all_content=result['all_content']
                )
                
                combined_content = dummy_result.get_content_for_fields(context.content_fields)
                if combined_content:
                    parts.append(combined_content)
                else:
                    parts.append("[Aucun contenu disponible pour les champs sélectionnés]")
                    
                if result['has_image']:
                    if context.should_send_images:
                        parts.append("[Cette source contient des éléments visuels - images fournies séparément]")
                    else:
                        parts.append("[Cette source contient des éléments visuels - non incluses]")
                parts.append("")
        
        return "\n".join(parts)