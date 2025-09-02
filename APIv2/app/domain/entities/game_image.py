from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ImageProcessingStatus(Enum):
    """Available processing status for an image"""

    UPLOADED = "uploaded"  # Fichier uploadé, en attente
    PROCESSING = "processing"  # En cours de traitement IA
    COMPLETED = "completed"  # Traitement terminé avec succès
    FAILED = "failed"  # Échec du traitement
    RETRYING = "retrying"  # Nouvel essai en cours


@dataclass
class GameImage:
    """An image for game rules"""

    id: UUID
    game_id: UUID
    file_path: str
    blob_url: str
    original_filename: Optional[str]
    file_size: int
    processing_status: ImageProcessingStatus
    processing_error: Optional[str]  # Message d'erreur si échec
    retry_count: int
    uploaded_by: UUID
    batch_id: Optional[UUID]  # Référence vers le batch parent (None pour images individuelles)
    created_at: datetime
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        game_id: UUID,
        file_path: str,
        blob_url: str,
        original_filename: str,
        file_size: int,
        uploaded_by: UUID,
        batch_id: Optional[UUID] = None
    ) -> 'GameImage':
        """Creates a new game image"""

        return cls(
            id=uuid4(),
            game_id=game_id,
            file_path=file_path,
            blob_url=blob_url,
            original_filename=original_filename,
            file_size=file_size,
            processing_status=ImageProcessingStatus.UPLOADED,
            processing_error=None,
            retry_count=0,
            uploaded_by=uploaded_by,
            batch_id=batch_id,
            created_at=datetime.now(timezone.utc),
            processing_started_at=None,
            processing_completed_at=None
        )