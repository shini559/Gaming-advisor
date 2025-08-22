import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.adapters.database.connection import Base
from app.shared.utils.datetime_utils import utc_now


class GameImageModel(Base):
    __tablename__ = "game_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relations
    game = relationship("GameModel", back_populates="images")
    uploader = relationship("UserModel")
    vectors = relationship("GameVectorModel", back_populates="image")