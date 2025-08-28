from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models.game_image import GameImageModel
from app.domain.entities.game_image import GameImage, ImageProcessingStatus
from app.domain.ports.repositories.game_image_repository import IGameImageRepository


class GameImageRepository(IGameImageRepository):
  def __init__(self, session: AsyncSession):
      self._session = session

  async def create(self, image: GameImage) -> GameImage:
      """Crée une nouvelle image en base"""
      model = GameImageModel(
          id=image.id,
          game_id=image.game_id,
          file_path=image.file_path,
          blob_url=image.blob_url,
          original_filename=image.original_filename,
          file_size=image.file_size,
          uploaded_by=image.uploaded_by,
          processing_status=image.processing_status,
          processing_error=image.processing_error,
          retry_count=image.retry_count,
          batch_id=image.batch_id,
          created_at=image.created_at,
          processing_started_at=image.processing_started_at,
          processing_completed_at=image.processing_completed_at
      )

      self._session.add(model)
      await self._session.flush()
      return self._model_to_entity(model)

  async def get_by_id(self, image_id: UUID) -> Optional[GameImage]:
      """Récupère une image par son ID"""
      stmt = select(GameImageModel).where(GameImageModel.id == image_id)
      result = await self._session.execute(stmt)
      model = result.scalar_one_or_none()
      return self._model_to_entity(model) if model else None

  async def get_by_game_id(self, game_id: UUID) -> List[GameImage]:
      """Récupère toutes les images d'un jeu"""
      stmt = select(GameImageModel).where(
          GameImageModel.game_id == game_id
      ).order_by(GameImageModel.created_at.desc())

      result = await self._session.execute(stmt)
      models = result.scalars().all()
      return [self._model_to_entity(model) for model in models]

  async def get_by_status(self, status: ImageProcessingStatus) -> List[GameImage]:
      """Récupère les images par statut de traitement"""
      stmt = select(GameImageModel).where(
          GameImageModel.processing_status == status
      ).order_by(GameImageModel.created_at.asc())

      result = await self._session.execute(stmt)
      models = result.scalars().all()
      return [self._model_to_entity(model) for model in models]

  async def update(self, image: GameImage) -> GameImage:
      """Met à jour une image"""
      stmt = select(GameImageModel).where(GameImageModel.id == image.id)
      result = await self._session.execute(stmt)
      model = result.scalar_one_or_none()

      if not model:
          raise ValueError(f"Image {image.id} not found")

      # Mettre à jour les champs
      model.processing_status = image.processing_status
      model.processing_error = image.processing_error
      model.retry_count = image.retry_count
      model.processing_started_at = image.processing_started_at
      model.processing_completed_at = image.processing_completed_at

      await self._session.flush()
      return self._model_to_entity(model)

  async def delete(self, image_id: UUID) -> bool:
      """Supprime une image"""
      stmt = select(GameImageModel).where(GameImageModel.id == image_id)
      result = await self._session.execute(stmt)
      model = result.scalar_one_or_none()

      if model:
          await self._session.delete(model)
          return True
      return False

  def _model_to_entity(self, model: GameImageModel) -> GameImage:
      """Convertit un modèle en entité"""
      return GameImage(
          id=model.id,
          game_id=model.game_id,
          file_path=model.file_path,
          blob_url=model.blob_url,
          original_filename=model.original_filename,
          file_size=model.file_size,
          uploaded_by=model.uploaded_by,
          processing_status=model.processing_status,
          processing_error=model.processing_error,
          retry_count=model.retry_count,
          batch_id=model.batch_id,
          created_at=model.created_at,
          processing_started_at=model.processing_started_at,
          processing_completed_at=model.processing_completed_at
      )