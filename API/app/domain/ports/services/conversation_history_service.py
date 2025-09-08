from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.entities.chat_message import ChatMessage


class IConversationHistoryService(ABC):
    """
    Interface pour le service d'historique de conversation avec feedback
    
    Cette interface permet de récupérer les messages d'une conversation
    enrichis avec les feedbacks associés sans créer de dépendances N+1
    """
    
    @abstractmethod
    async def get_conversation_history_with_feedback(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Récupère l'historique d'une conversation avec les feedbacks associés
        
        Args:
            conversation_id: ID de la conversation
            limit: Nombre maximum de messages à retourner
            offset: Décalage pour la pagination
            
        Returns:
            Liste des messages avec le champ is_useful rempli selon les feedbacks
            
        Performance: 2 requêtes optimisées + mapping O(n)
        """
        pass
    
    @abstractmethod
    async def get_conversation_history_for_agent(
        self,
        conversation_id: UUID, 
        limit_messages: int = 20,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Version simple pour l'agent IA (pas besoin des feedbacks)
        
        Args:
            conversation_id: ID de la conversation
            limit_messages: Nombre de messages pour le contexte IA
            offset: Décalage pour la pagination
            
        Returns:
            Liste des messages sans enrichissement feedback
        """
        pass