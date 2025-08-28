from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.connection import Base
from app.domain.entities.chat_message import MessageRole


class ChatMessageModel(Base):
    """Modèle SQLAlchemy pour les messages de chat"""
    
    __tablename__ = "chat_messages"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chat_conversations.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: [])  # Stocké comme JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relations
    conversation: Mapped["ChatConversationModel"] = relationship("ChatConversationModel", back_populates="messages")
    feedbacks: Mapped[list["ChatFeedbackModel"]] = relationship("ChatFeedbackModel", back_populates="message", cascade="all, delete-orphan")