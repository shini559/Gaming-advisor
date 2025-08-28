from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


class MessageRole(str, Enum):
    """Rôle du message dans la conversation"""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class MessageSource:
    """Source d'information utilisée par l'agent pour générer la réponse"""
    
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
        return cls(
            vector_id=vector_id,
            image_id=image_id,
            similarity_score=similarity_score,
            content_snippet=content_snippet,
            image_url=image_url
        )


@dataclass
class ChatMessage:
    """Message dans une conversation de chat avec l'agent IA"""
    
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    sources: List[MessageSource]
    created_at: datetime
    
    @classmethod
    def create_user_message(
        cls,
        conversation_id: UUID,
        content: str,
        message_id: Optional[UUID] = None
    ) -> 'ChatMessage':
        """Factory method pour créer un message utilisateur"""
        return cls(
            id=message_id or uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            sources=[],  # Les messages utilisateur n'ont pas de sources
            created_at=datetime.utcnow()
        )
    
    @classmethod
    def create_assistant_message(
        cls,
        conversation_id: UUID,
        content: str,
        sources: List[MessageSource],
        message_id: Optional[UUID] = None
    ) -> 'ChatMessage':
        """Factory method pour créer un message de l'assistant"""
        return cls(
            id=message_id or uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            sources=sources,
            created_at=datetime.utcnow()
        )
    
    def is_from_user(self) -> bool:
        """Vérifie si le message provient de l'utilisateur"""
        return self.role == MessageRole.USER
    
    def is_from_assistant(self) -> bool:
        """Vérifie si le message provient de l'assistant"""
        return self.role == MessageRole.ASSISTANT
    
    def has_sources(self) -> bool:
        """Vérifie si le message a des sources (uniquement pour l'assistant)"""
        return len(self.sources) > 0
    
    def get_sources_summary(self) -> str:
        """Retourne un résumé des sources utilisées"""
        if not self.has_sources():
            return "Aucune source"
        
        return f"{len(self.sources)} source(s) utilisée(s)"