from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Integer, DateTime, Enum as SqlEnum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.data.connection import Base
from app.domain.entities.game_image import ImageProcessingStatus


class GameImageModel(Base):
    """SQLAlchemy model for game images"""

    __tablename__ = "game_images"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("image_batches.id"), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    blob_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    processing_status: Mapped[ImageProcessingStatus] = mapped_column(
        SqlEnum(ImageProcessingStatus),
        default=ImageProcessingStatus.UPLOADED,
        nullable=False
    )
    processing_error: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    processing_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    game = relationship("GameModel", back_populates="images")
    batch = relationship("ImageBatchModel", back_populates="images")
    uploader = relationship("UserModel")
    vectors = relationship("GameVectorModel", back_populates="image")