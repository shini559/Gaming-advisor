from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.adapters.database.connection import Base
from app.shared.utils.datetime_utils import utc_now


class GameModel(Base):
    __tablename__ = 'games'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    series_id = Column(UUID(as_uuid=True), ForeignKey('game_series.id'), nullable=True)
    is_expansion = Column(Boolean, default=False, nullable=False)
    base_game_id = Column(UUID(as_uuid=True), ForeignKey('games.id'), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relations
    series = relationship("GameSeriesModel", back_populates="games")
    base_game = relationship("GameModel", remote_side=[id], back_populates="expansions")
    expansions = relationship("GameModel", back_populates="base_game")
    creator = relationship("UserModel")
    images = relationship("GameImageModel", back_populates="game")
    vectors = relationship("GameVectorModel", back_populates="game")