from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class FeedbackType(str, Enum):
    """Available types of feedback"""
    POSITIVE = "positive"
    NEGATIVE = "negative"


@dataclass
class ChatFeedback:
    """User feedback to an AI agent response"""
    
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
        """Factory method to create a feedback"""
        now = datetime.now(timezone.utc)
        return cls(
            id=feedback_id or uuid4(),
            message_id=message_id,
            feedback_type=feedback_type,
            comment=comment,
            created_at=now
        )
    
    def update_feedback(
        self, 
        feedback_type: FeedbackType, 
        comment: Optional[str] = None
    ) -> None:
        """Updates feedback"""
        self.feedback_type = feedback_type
        self.comment = comment