from typing import List


from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Text, DateTime, Integer
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.data.connection import Base


class GameVectorModel(Base):
    __tablename__ = "game_vectors"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    image_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("game_images.id"), nullable=False)
    vector_embedding: Mapped[List[float]] = mapped_column(Vector(1536), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    # Relations
    game = relationship("GameModel", back_populates="vectors")
    image = relationship("GameImageModel", back_populates="vectors")