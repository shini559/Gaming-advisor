from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.data.connection import Base


class GameModel(Base):
    __tablename__ = 'games'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    series_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('game_series.id'), nullable=True)
    is_expansion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    base_game_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('games.id'), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Relations
    series = relationship("GameSeriesModel", back_populates="games")
    base_game = relationship("GameModel", remote_side=[id], back_populates="expansions")
    expansions = relationship("GameModel", back_populates="base_game")
    creator = relationship("UserModel")
    images = relationship("GameImageModel", back_populates="game")
    image_batches = relationship("ImageBatchModel", back_populates="game")
    vectors = relationship("GameVectorModel", back_populates="game")