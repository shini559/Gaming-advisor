from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.data.connection import Base


class GameSeriesModel(Base):
    __tablename__ = 'game_series'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Relations
    games = relationship("GameModel", back_populates="series")