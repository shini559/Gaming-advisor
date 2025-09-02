from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat_message import ChatMessage, MessageRole


class IChatMessageRepository(ABC):
    """Interface pour le repository des messages de chat"""
    
    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage:
        """Créer un nouveau message"""
        pass
    
    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Optional[ChatMessage]:
        """Récupérer un message par son ID"""
        pass
    
    @abstractmethod
    async def get_by_conversation_id(self, conversation_id: UUID, limit: int = 50, offset: int = 0) -> List[ChatMessage]:
        """Récupérer les messages d'une conversation avec pagination (triés par date croissante)"""
        pass
    
    @abstractmethod
    async def count_by_conversation_id(self, conversation_id: UUID) -> int:
        """Compter les messages d'une conversation"""
        pass
    
    @abstractmethod
    async def count_by_conversation(self, conversation_id: UUID) -> int:
        """Compter les messages d'une conversation (alias pour cohérence)"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, conversation_id: UUID, limit_messages: int = 20) -> List[ChatMessage]:
        """Récupérer les derniers messages d'une conversation pour le contexte IA"""
        pass
    
    @abstractmethod
    async def get_by_role(self, conversation_id: UUID, role: MessageRole) -> List[ChatMessage]:
        """Récupérer les messages d'un rôle spécifique dans une conversation"""
        pass
    
    @abstractmethod
    async def delete_by_conversation_id(self, conversation_id: UUID) -> int:
        """Supprimer tous les messages d'une conversation (retourne le nombre supprimé)"""
        pass
    
    @abstractmethod
    async def update(self, message: ChatMessage) -> ChatMessage:
        """Mettre à jour un message (rarement utilisé)"""
        pass