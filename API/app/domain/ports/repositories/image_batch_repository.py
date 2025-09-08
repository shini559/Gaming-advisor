from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities.image_batch import ImageBatch


class IImageBatchRepository(ABC):
    """Interface pour la persistence des batches d'images"""

    @abstractmethod
    async def create(self, batch: ImageBatch) -> ImageBatch:
        """Créer un nouveau batch en base"""
        pass

    @abstractmethod
    async def get_by_id(self, batch_id: UUID) -> Optional[ImageBatch]:
        """Récupérer un batch par son ID"""
        pass

    @abstractmethod  
    async def update(self, batch: ImageBatch) -> ImageBatch:
        """Mettre à jour un batch existant"""
        pass

    @abstractmethod
    async def get_by_game_id(self, game_id: UUID, limit: int = 50) -> List[ImageBatch]:
        """Récupérer les batches d'un jeu"""
        pass

    @abstractmethod
    async def get_pending_batches(self) -> List[ImageBatch]:
        """Récupérer les batches en attente de traitement"""
        pass

    @abstractmethod
    async def get_retryable_batches(self) -> List[ImageBatch]:
        """Récupérer les batches qui peuvent être retriés"""
        pass

    @abstractmethod
    async def delete(self, batch_id: UUID) -> bool:
        """Supprimer un batch"""
        pass