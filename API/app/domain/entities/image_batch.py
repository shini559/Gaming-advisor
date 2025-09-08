from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class BatchStatus(str, Enum):
    """Available statuses for an image batch"""
    PENDING = "pending"                    # Créé, pas encore commencé
    PROCESSING = "processing"              # En cours de traitement
    COMPLETED = "completed"                # Terminé avec succès (toutes images traitées)
    FAILED = "failed"                     # Échec définitif (trop de retries)
    RETRYING = "retrying"                 # En cours de retry des images échouées
    PARTIALLY_COMPLETED = "partially_completed"  # Terminé avec quelques échecs définitifs


@dataclass
class ImageBatch:
    """An image batch"""
    
    id: UUID
    game_id: UUID
    total_images: int
    processed_images: int
    failed_images: int
    status: BatchStatus
    retry_count: int
    max_retries: int
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        game_id: UUID,
        total_images: int,
        max_retries: int
    ) -> 'ImageBatch':
        """Factory method to create an image batch"""
        if total_images <= 0:
            raise ValueError("There must be at least one image in the batch")
            
        return cls(
            id=uuid4(),
            game_id=game_id,
            total_images=total_images,
            processed_images=0,
            failed_images=0,
            status=BatchStatus.PENDING,
            retry_count=0,
            max_retries=max_retries,
            created_at=datetime.now(timezone.utc)
        )

    @property
    def progress_ratio(self) -> str:
        """Batch success ratio"""
        return f"{self.processed_images}/{self.total_images}"
    
    @property
    def failed_ratio(self) -> str:
        """Batch failure ratio"""
        return f"{self.failed_images}/{self.total_images}"
    
    @property
    def completion_percentage(self) -> float:
        """Batch completion percentage"""
        if self.total_images == 0:
            return 0.0
        return (self.processed_images / self.total_images) * 100
    
    @property
    def failure_percentage(self) -> float:
        """Batch failure percentage"""
        if self.total_images == 0:
            return 0.0
        return (self.failed_images / self.total_images) * 100

    # Business methods
    def can_retry(self) -> bool:
        """Checks if the batch failures can be retried"""
        return self.retry_count < self.max_retries and self.failed_images > 0