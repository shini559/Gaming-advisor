from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat_conversation import ChatConversation


class IChatConversationRepository(ABC):
    """Interface pour le repository des conversations de chat"""
    
    @abstractmethod
    async def create(self, conversation: ChatConversation) -> ChatConversation:
        """Créer une nouvelle conversation"""
        pass
    
    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Optional[ChatConversation]:
        """Récupérer une conversation par son ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ChatConversation]:
        """Récupérer les conversations d'un utilisateur avec pagination"""
        pass
    
    @abstractmethod
    async def get_by_game_and_user(self, game_id: UUID, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ChatConversation]:
        """Récupérer les conversations d'un utilisateur pour un jeu spécifique"""
        pass
    
    @abstractmethod
    async def count_by_user_id(self, user_id: UUID) -> int:
        """Compter les conversations d'un utilisateur"""
        pass
    
    @abstractmethod
    async def count_by_game_and_user(self, game_id: UUID, user_id: UUID) -> int:
        """Compter les conversations d'un utilisateur pour un jeu spécifique"""
        pass
    
    @abstractmethod
    async def update(self, conversation: ChatConversation) -> ChatConversation:
        """Mettre à jour une conversation"""
        pass
    
    @abstractmethod
    async def delete(self, conversation_id: UUID) -> bool:
        """Supprimer une conversation et tous ses messages"""
        pass
    
    @abstractmethod
    async def exists_for_user(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Vérifier si une conversation appartient à un utilisateur"""
        pass