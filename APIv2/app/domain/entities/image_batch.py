from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class BatchStatus(str, Enum):
    """Statut d'un batch d'images"""
    PENDING = "pending"                    # Créé, pas encore commencé
    PROCESSING = "processing"              # En cours de traitement
    COMPLETED = "completed"                # Terminé avec succès (toutes images traitées)
    FAILED = "failed"                     # Échec définitif (trop de retries)
    RETRYING = "retrying"                 # En cours de retry des images échouées
    PARTIALLY_COMPLETED = "partially_completed"  # Terminé avec quelques échecs définitifs


@dataclass
class ImageBatch:
    """Entité Domain représentant un batch d'images à traiter"""
    
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
        """Créer un nouveau batch d'images"""
        if total_images <= 0:
            raise ValueError("Le nombre d'images doit être supérieur à 0")
            
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

    # Properties pour les ratios et pourcentages
    @property
    def progress_ratio(self) -> str:
        """Ratio de progression : '5/30'"""
        return f"{self.processed_images}/{self.total_images}"
    
    @property
    def failed_ratio(self) -> str:
        """Ratio d'échecs : '2/30'"""
        return f"{self.failed_images}/{self.total_images}"
    
    @property
    def completion_percentage(self) -> float:
        """Pourcentage de completion : 16.67"""
        if self.total_images == 0:
            return 0.0
        return (self.processed_images / self.total_images) * 100
    
    @property
    def failure_percentage(self) -> float:
        """Pourcentage d'échecs : 6.67"""
        if self.total_images == 0:
            return 0.0
        return (self.failed_images / self.total_images) * 100

    # Business methods
    def can_retry(self) -> bool:
        """Vérifie si le batch peut être retrié"""
        return self.retry_count < self.max_retries and self.failed_images > 0

    def is_completed(self) -> bool:
        """Vérifie si le batch est terminé (avec ou sans échecs)"""
        return (self.processed_images + self.failed_images) == self.total_images

    def mark_image_processed(self) -> None:
        """Marquer une image comme traitée avec succès"""
        if self.processed_images >= self.total_images:
            raise ValueError("Impossible de marquer plus d'images que le total")
        self.processed_images += 1
        self._update_status_if_needed()

    def mark_image_failed(self) -> None:
        """Marquer une image comme échouée"""
        if self.failed_images >= self.total_images:
            raise ValueError("Impossible de marquer plus d'images que le total")
        self.failed_images += 1
        self._update_status_if_needed()

    def start_processing(self) -> None:
        """Démarrer le traitement du batch"""
        if self.status != BatchStatus.PENDING:
            raise ValueError(f"Impossible de démarrer le traitement depuis le statut {self.status}")
        
        self.status = BatchStatus.PROCESSING
        self.processing_started_at = datetime.now(timezone.utc)

    def start_retry(self) -> None:
        """Démarrer un retry du batch"""
        if not self.can_retry():
            raise ValueError("Impossible de retry : nombre maximum de retries atteint ou pas d'échecs")
        
        # Reset des compteurs pour retry
        retry_images = self.failed_images
        self.processed_images += retry_images  # Les images précédemment réussies restent comptées
        self.failed_images = 0  # Reset des échecs pour nouveau try
        self.retry_count += 1
        self.status = BatchStatus.RETRYING

    def complete(self) -> None:
        """Marquer le batch comme terminé"""
        self.completed_at = datetime.now(timezone.utc)
        
        if self.failed_images == 0:
            self.status = BatchStatus.COMPLETED
        elif self.can_retry():
            # Des échecs mais retries encore possibles - ne pas marquer comme terminé
            pass
        else:
            # Des échecs et plus de retries possibles
            self.status = BatchStatus.PARTIALLY_COMPLETED if self.processed_images > 0 else BatchStatus.FAILED

    def _update_status_if_needed(self) -> None:
        """Met à jour le statut si le batch est terminé"""
        if self.is_completed():
            self.complete()