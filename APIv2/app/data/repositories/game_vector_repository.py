from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import GameVectorModel
from app.domain.entities.game_vector import GameVector
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository


class GameVectorRepository(IGameVectorRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, vector: GameVector) -> GameVector:
        model = GameVectorModel(
            id=vector.id,
            game_id=vector.game_id,
            image_id=vector.image_id,
            vector_embedding=vector.vector_embedding,
            extracted_text=vector.extracted_text,
            page_number=vector.page_number
        )
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)

    async def get_by_id(self, vector_id: UUID) -> Optional[GameVector]:
        stmt = select(GameVectorModel).where(GameVectorModel.id == vector_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_game(self, game_id: UUID) -> List[GameVector]:
        stmt = select(GameVectorModel).where(GameVectorModel.game_id == game_id).order_by(GameVectorModel.created_at)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_image(self, image_id: UUID) -> List[GameVector]:
        stmt = select(GameVectorModel).where(GameVectorModel.image_id == image_id).order_by(GameVectorModel.page_number)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def update(self, vector: GameVector) -> GameVector:
        stmt = select(GameVectorModel).where(GameVectorModel.id == vector.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.vector_embedding = vector.vector_embedding
        model.extracted_text = vector.extracted_text
        model.page_number = vector.page_number

        await self._session.flush()
        return self._model_to_entity(model)

    async def delete(self, vector_id: UUID) -> bool:
        stmt = select(GameVectorModel).where(GameVectorModel.id == vector_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            return True
        return False

    def _model_to_entity(self, model: GameVectorModel) -> GameVector:
        return GameVector(
            id=model.id,
            game_id=model.game_id,
            image_id=model.image_id,
            vector_embedding=model.vector_embedding,
            extracted_text=model.extracted_text,
            page_number=model.page_number,
            created_at=model.created_at
        )