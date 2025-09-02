from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class ChatConversation:
    """Entité représentant une conversation de chat avec l'agent IA"""
    
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
        """Factory method pour créer une nouvelle conversation"""
        now = datetime.utcnow()
        
        return cls(
            id=conversation_id or uuid4(),
            game_id=game_id,
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now
        )
    
    def update_title(self, new_title: str) -> None:
        """Met à jour le titre de la conversation"""
        self.title = new_title
        self.updated_at = datetime.utcnow()
    
    def touch(self) -> None:
        """Met à jour le timestamp updated_at (utilisé lors d'ajout de messages)"""
        self.updated_at = datetime.utcnow()
    
    def is_owned_by(self, user_id: UUID) -> bool:
        """Vérifie si la conversation appartient à l'utilisateur"""
        return self.user_id == user_id