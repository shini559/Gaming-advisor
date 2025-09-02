from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.connection import Base


class ChatFeedbackModel(Base):
    """Modèle SQLAlchemy pour le feedback des messages de chat"""
    
    __tablename__ = "chat_feedbacks"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    is_helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relations
    message: Mapped["ChatMessageModel"] = relationship("ChatMessageModel", back_populates="feedbacks")