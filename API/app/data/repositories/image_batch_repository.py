from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.data.models.image_batch import ImageBatchModel
from app.domain.entities.image_batch import ImageBatch, BatchStatus
from app.domain.ports.repositories.image_batch_repository import IImageBatchRepository


class ImageBatchRepository(IImageBatchRepository):
    """Implémentation repository pour les batches d'images"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, batch: ImageBatch) -> ImageBatch:
        """Créer un nouveau batch en base"""
        model = ImageBatchModel(
            id=batch.id,
            game_id=batch.game_id,
            total_images=batch.total_images,
            processed_images=batch.processed_images,
            failed_images=batch.failed_images,
            status=batch.status,
            retry_count=batch.retry_count,
            max_retries=batch.max_retries,
            created_at=batch.created_at,
            processing_started_at=batch.processing_started_at,
            completed_at=batch.completed_at
        )
        
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        
        return self._model_to_entity(model)

    async def get_by_id(self, batch_id: UUID) -> Optional[ImageBatch]:
        """Récupérer un batch par son ID"""
        query = select(ImageBatchModel).where(ImageBatchModel.id == batch_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        return self._model_to_entity(model) if model else None

    async def update(self, batch: ImageBatch) -> ImageBatch:
        """Mettre à jour un batch existant"""
        query = select(ImageBatchModel).where(ImageBatchModel.id == batch.id)
        result = await self.session.execute(query)
        model = result.scalar_one()
        
        # Mettre à jour les champs
        model.processed_images = batch.processed_images
        model.failed_images = batch.failed_images
        model.status = batch.status
        model.retry_count = batch.retry_count
        model.processing_started_at = batch.processing_started_at
        model.completed_at = batch.completed_at
        
        await self.session.flush()
        await self.session.refresh(model)
        
        return self._model_to_entity(model)

    async def get_by_game_id(self, game_id: UUID, limit: int = 50) -> List[ImageBatch]:
        """Récupérer les batches d'un jeu"""
        query = (
            select(ImageBatchModel)
            .where(ImageBatchModel.game_id == game_id)
            .order_by(ImageBatchModel.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]

    async def get_pending_batches(self) -> List[ImageBatch]:
        """Récupérer les batches en attente de traitement"""
        query = (
            select(ImageBatchModel)
            .where(ImageBatchModel.status == BatchStatus.PENDING)
            .order_by(ImageBatchModel.created_at.asc())
        )
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]

    async def get_retryable_batches(self) -> List[ImageBatch]:
        """Récupérer les batches qui peuvent être retriés"""
        query = (
            select(ImageBatchModel)
            .where(
                and_(
                    ImageBatchModel.failed_images > 0,
                    ImageBatchModel.retry_count < ImageBatchModel.max_retries,
                    ImageBatchModel.status.in_([BatchStatus.COMPLETED, BatchStatus.PARTIALLY_COMPLETED])
                )
            )
            .order_by(ImageBatchModel.created_at.asc())
        )
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in models]

    async def delete(self, batch_id: UUID) -> bool:
        """Supprimer un batch"""
        query = select(ImageBatchModel).where(ImageBatchModel.id == batch_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            return True
        
        return False

    def _model_to_entity(self, model: ImageBatchModel) -> ImageBatch:
        """Convertir un modèle en entité Domain"""
        return ImageBatch(
            id=model.id,
            game_id=model.game_id,
            total_images=model.total_images,
            processed_images=model.processed_images,
            failed_images=model.failed_images,
            status=model.status,
            retry_count=model.retry_count,
            max_retries=model.max_retries,
            created_at=model.created_at,
            processing_started_at=model.processing_started_at,
            completed_at=model.completed_at
        )