from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.connection import Base

if TYPE_CHECKING:
      from app.data.models.user import UserModel
      from app.data.models.game import GameModel
      from app.data.models.chat_message import ChatMessageModel



class ChatConversationModel(Base):
    """SQLAlchemy model for chat conversations"""
    
    __tablename__ = "chat_conversations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relations
    messages: Mapped[list["ChatMessageModel"]] = relationship("ChatMessageModel", back_populates="conversation", cascade="all, delete-orphan")
    game: Mapped["GameModel"] = relationship("GameModel")
    user: Mapped["UserModel"] = relationship("UserModel")