from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat_feedback import ChatFeedback


class IChatFeedbackRepository(ABC):
    """Interface pour le repository du feedback des messages de chat"""
    
    @abstractmethod
    async def create(self, feedback: ChatFeedback) -> ChatFeedback:
        """Créer un nouveau feedback"""
        pass
    
    @abstractmethod
    async def get_by_id(self, feedback_id: UUID) -> Optional[ChatFeedback]:
        """Récupérer un feedback par son ID"""
        pass
    
    @abstractmethod
    async def get_by_message_id(self, message_id: UUID) -> Optional[ChatFeedback]:
        """Récupérer le feedback d'un message (un seul feedback par message)"""
        pass
    
    @abstractmethod
    async def get_by_message_and_user(self, message_id: UUID, user_id: UUID) -> Optional[ChatFeedback]:
        """Récupérer le feedback d'un message pour un utilisateur spécifique"""
        pass
    
    @abstractmethod
    async def get_by_conversation_id(self, conversation_id: UUID) -> List[ChatFeedback]:
        """Récupérer tous les feedbacks d'une conversation"""
        pass
    
    @abstractmethod
    async def update(self, feedback: ChatFeedback) -> ChatFeedback:
        """Mettre à jour un feedback existant"""
        pass
    
    @abstractmethod
    async def delete(self, feedback_id: UUID) -> bool:
        """Supprimer un feedback"""
        pass
    
    @abstractmethod
    async def exists_for_message(self, message_id: UUID) -> bool:
        """Vérifier si un message a déjà un feedback"""
        pass
    
    @abstractmethod
    async def get_positive_feedback_count(self, conversation_id: UUID) -> int:
        """Compter les feedbacks positifs d'une conversation"""
        pass
    
    @abstractmethod
    async def get_negative_feedback_count(self, conversation_id: UUID) -> int:
        """Compter les feedbacks négatifs d'une conversation"""
        pass