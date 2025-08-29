from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class FeedbackType(str, Enum):
    """Types de feedback possibles"""
    POSITIVE = "positive"
    NEGATIVE = "negative"


@dataclass
class ChatFeedback:
    """Feedback utilisateur sur une réponse de l'agent IA"""
    
    id: UUID
    message_id: UUID
    feedback_type: FeedbackType
    comment: Optional[str]
    created_at: datetime
    
    @classmethod
    def create(
        cls,
        message_id: UUID,
        feedback_type: FeedbackType,
        comment: Optional[str] = None,
        feedback_id: Optional[UUID] = None
    ) -> 'ChatFeedback':
        """Factory method pour créer un feedback"""
        now = datetime.utcnow()
        return cls(
            id=feedback_id or uuid4(),
            message_id=message_id,
            feedback_type=feedback_type,
            comment=comment,
            created_at=now
        )
    
    def is_positive(self) -> bool:
        """Vérifie si le feedback est positif"""
        return self.feedback_type == FeedbackType.POSITIVE
    
    def is_negative(self) -> bool:
        """Vérifie si le feedback est négatif"""
        return self.feedback_type == FeedbackType.NEGATIVE
    
    def has_comment(self) -> bool:
        """Vérifie si le feedback contient un commentaire"""
        return self.comment is not None and len(self.comment.strip()) > 0
    
    def update_feedback(
        self, 
        feedback_type: FeedbackType, 
        comment: Optional[str] = None
    ) -> None:
        """Met à jour le feedback"""
        self.feedback_type = feedback_type
        self.comment = comment