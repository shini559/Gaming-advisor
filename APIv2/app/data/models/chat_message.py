from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.connection import Base
from app.domain.entities.chat_message import MessageRole

if TYPE_CHECKING:
      from app.data.models.chat_feedback import ChatFeedbackModel
      from app.data.models.chat_conversation import ChatConversationModel

class ChatMessageModel(Base):
    """SQLAlchemy Model for chat messages"""
    
    __tablename__ = "chat_messages"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chat_conversations.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: [])
    search_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # Relations
    conversation: Mapped["ChatConversationModel"] = relationship("ChatConversationModel", back_populates="messages")
    feedbacks: Mapped[list["ChatFeedbackModel"]] = relationship("ChatFeedbackModel", back_populates="message", cascade="all, delete-orphan")