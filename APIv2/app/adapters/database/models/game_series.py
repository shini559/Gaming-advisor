import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.adapters.database.connection import Base
from app.shared.utils.datetime_utils import utc_now


class GameSeriesModel(Base):
    __tablename__ = 'game_series'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relations
    games = relationship("GameModel", back_populates="series")