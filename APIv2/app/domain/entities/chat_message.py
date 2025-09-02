from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


class MessageRole(str, Enum):
    """Available message roles in the conversation"""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class MessageSource:
    """Information source used by the agent to make its answer"""
    
    vector_id: UUID
    image_id: Optional[UUID]
    similarity_score: float
    content_snippet: str
    image_url: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        vector_id: UUID,
        similarity_score: float,
        content_snippet: str,
        image_id: Optional[UUID] = None,
        image_url: Optional[str] = None
    ) -> 'MessageSource':
        """Factory method to create a source"""
        return cls(
            vector_id=vector_id,
            image_id=image_id,
            similarity_score=similarity_score,
            content_snippet=content_snippet,
            image_url=image_url
        )


@dataclass
class ChatMessage:
    """Chat message with the AI agent"""
    
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    sources: List[MessageSource]
    created_at: datetime
    search_method: Optional[str] = None  # Méthode de recherche utilisée (ocr, description, labels, hybrid)
    is_useful: Optional[bool] = None  # Feedback utilisateur (None=pas de feedback, True=positif, False=négatif)
    
    @classmethod
    def create_user_message(
        cls,
        conversation_id: UUID,
        content: str,
        message_id: Optional[UUID] = None
    ) -> 'ChatMessage':
        """Factory method to create a user message"""
        return cls(
            id=message_id or uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            sources=[],  # Les messages utilisateur n'ont pas de sources
            created_at=datetime.now(timezone.utc)
        )
    
    @classmethod
    def create_assistant_message(
        cls,
        conversation_id: UUID,
        content: str,
        sources: List[MessageSource],
        search_method: Optional[str] = None,
        message_id: Optional[UUID] = None
    ) -> 'ChatMessage':
        """Factory method to create an agent message"""
        return cls(
            id=message_id or uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            sources=sources,
            created_at=datetime.now(timezone.utc),
            search_method=search_method
        )
    
    def is_from_user(self) -> bool:
        """Checks if the message is from user"""
        return self.role == MessageRole.USER
    
    def is_from_assistant(self) -> bool:
        """Checks if the message is from agent"""
        return self.role == MessageRole.ASSISTANT
    
    def has_sources(self) -> bool:
        """Checks if the message has sources"""
        return len(self.sources) > 0