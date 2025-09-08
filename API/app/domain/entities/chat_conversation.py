from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class ChatConversation:
    """Entity for a chat conversation with tha AI agent"""
    
    id: UUID
    game_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def create(
        cls,
        game_id: UUID,
        user_id: UUID,
        title: str,
        conversation_id: Optional[UUID] = None
    ) -> 'ChatConversation':
        """Factory method to create a new conversation"""
        now = datetime.now(timezone.utc)
        
        return cls(
            id=conversation_id or uuid4(),
            game_id=game_id,
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now
        )
    
    def touch(self) -> None:
        """Updates the updated_at timestamp (use when adding messages)"""
        self.updated_at = datetime.now(timezone.utc)