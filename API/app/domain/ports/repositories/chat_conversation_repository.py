from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat_conversation import ChatConversation


class IChatConversationRepository(ABC):
    """Interface for chat conversations repository"""
    
    @abstractmethod
    async def create(self, conversation: ChatConversation) -> ChatConversation:
        """Creates a new conversation"""
        pass
    
    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Optional[ChatConversation]:
        """Gets a conversation by its ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ChatConversation]:
        """Gets a user's conversations by his ID (paginated))"""
        pass
    
    @abstractmethod
    async def get_by_game_and_user(self, game_id: UUID, user_id: UUID, limit: int = 50, offset: int = 0) -> List[ChatConversation]:
        """Gets a user's conversations for a specific game by their ID (paginated)"""
        pass
    
    @abstractmethod
    async def count_by_user_id(self, user_id: UUID) -> int:
        """Count a user's conversations by his ID"""
        pass
    
    @abstractmethod
    async def count_by_game_and_user(self, game_id: UUID, user_id: UUID) -> int:
        """Count a user's conversations for a specific game by their IDs"""
        pass
    
    @abstractmethod
    async def update(self, conversation: ChatConversation) -> ChatConversation:
        """Updates a conversation title"""
        pass
    
    @abstractmethod
    async def delete(self, conversation_id: UUID) -> bool:
        """Deletes a conversation by its ID"""
        pass
    
    @abstractmethod
    async def exists_for_user(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Checks if a conversation is associated with a specific user by their IDs"""
        pass