from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Integer, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.data.connection import Base


class GameImageModel(Base):
    __tablename__ = "game_images"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    # Relations
    game = relationship("GameModel", back_populates="images")
    uploader = relationship("UserModel")
    vectors = relationship("GameVectorModel", back_populates="image")