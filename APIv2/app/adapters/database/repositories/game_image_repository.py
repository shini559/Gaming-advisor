from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.models import GameImageModel
from app.domain.entities.game_image import GameImage


class GameImageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, image: GameImage) -> GameImage:
        model = GameImageModel(
            id=image.id,
            game_id=image.game_id,
            file_path=image.file_path,
            original_filename=image.original_filename,
            file_size=image.file_size,
            uploaded_by=image.uploaded_by
        )
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)

    async def get_by_id(self, image_id: UUID) -> Optional[GameImage]:
        stmt = select(GameImageModel).where(GameImageModel.id == image_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_game(self, game_id: UUID) -> List[GameImage]:
        stmt = select(GameImageModel).where(GameImageModel.game_id == game_id).order_by(GameImageModel.created_at)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_uploader(self, user_id: UUID) -> List[GameImage]:
        stmt = select(GameImageModel).where(GameImageModel.uploaded_by == user_id).order_by(
            GameImageModel.created_at.desc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def update(self, image: GameImage) -> GameImage:
        stmt = select(GameImageModel).where(GameImageModel.id == image.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.file_path = image.file_path
        model.original_filename = image.original_filename
        model.file_size = image.file_size

        await self._session.flush()
        return self._model_to_entity(model)

    async def delete(self, image_id: UUID) -> bool:
        stmt = select(GameImageModel).where(GameImageModel.id == image_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            return True
        return False

    def _model_to_entity(self, model: GameImageModel) -> GameImage:
        return GameImage(
            id=model.id,
            game_id=model.game_id,
            file_path=model.file_path,
            original_filename=model.original_filename,
            file_size=model.file_size,
            uploaded_by=model.uploaded_by,
            created_at=model.created_at
        )