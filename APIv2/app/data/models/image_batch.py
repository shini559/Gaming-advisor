from sqlalchemy import Integer, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.data.connection import Base
from app.domain.entities.image_batch import BatchStatus


class ImageBatchModel(Base):
    """SQLAlchemy model for image batches"""
    
    __tablename__ = "image_batches"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    total_images: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_images: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_images: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(SqlEnum(BatchStatus), default=BatchStatus.PENDING, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    processing_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    game = relationship("GameModel", back_populates="image_batches")
    images = relationship("GameImageModel", back_populates="batch")