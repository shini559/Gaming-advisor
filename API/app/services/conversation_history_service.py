from typing import List
from uuid import UUID

from app.domain.entities.chat_message import ChatMessage
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository
from app.domain.ports.repositories.chat_feedback_repository import IChatFeedbackRepository
from app.domain.ports.services.conversation_history_service import IConversationHistoryService


class ConversationHistoryService(IConversationHistoryService):
    """
    Service pour récupérer l'historique des conversations avec les feedbacks associés
    
    Combine les données de messages et feedbacks en respectant la Clean Architecture :
    - 2 requêtes optimisées au lieu de N+1
    - Séparation des responsabilités entre repositories
    - Mapping en mémoire pour performance
    """
    
    def __init__(
        self,
        message_repository: IChatMessageRepository,
        feedback_repository: IChatFeedbackRepository
    ):
        self.message_repository = message_repository
        self.feedback_repository = feedback_repository
    
    async def get_conversation_history_with_feedback(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Récupère l'historique d'une conversation avec les feedbacks associés
        
        Performance : 2 requêtes optimisées + mapping O(n)
        """
        
        # 1. Récupérer tous les messages de la conversation
        messages = await self.message_repository.get_by_conversation_id(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
        
        if not messages:
            return messages
        
        # 2. Récupérer tous les feedbacks de la conversation en une seule requête
        feedbacks = await self.feedback_repository.get_by_conversation_id(conversation_id)
        
        # 3. Créer un mapping message_id -> feedback_type pour lookup O(1)
        from app.domain.entities.chat_feedback import FeedbackType
        feedback_map = {feedback.message_id: feedback.feedback_type for feedback in feedbacks}
        
        # 4. Enrichir chaque message avec son feedback (si existant)
        for message in messages:
            feedback_type = feedback_map.get(message.id)
            # Convertir FeedbackType vers is_useful (Optional[bool])
            if feedback_type is not None:
                message.is_useful = (feedback_type == FeedbackType.POSITIVE)
            else:
                message.is_useful = None  # Pas de feedback
        
        return messages
    
    async def get_conversation_history_for_agent(
        self,
        conversation_id: UUID, 
        limit_messages: int = 20,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Version simple pour l'agent IA (pas besoin des feedbacks)
        Délègue au repository directement
        """
        return await self.message_repository.get_conversation_history(
            conversation_id=conversation_id,
            limit_messages=limit_messages,
            offset=offset
        )