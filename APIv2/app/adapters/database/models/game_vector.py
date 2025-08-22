import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.adapters.database.connection import Base
from app.shared.utils.datetime_utils import utc_now


class GameVectorModel(Base):
    __tablename__ = "game_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("game_images.id"), nullable=False)
    vector_embedding = Column(Vector(1536), nullable=False)
    extracted_text = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relations
    game = relationship("GameModel", back_populates="vectors")
    image = relationship("GameImageModel", back_populates="vectors")