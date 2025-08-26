from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import GameSeriesModel
from app.domain.entities.game_series import GameSeries
from app.domain.ports.repositories.game_series_repository import IGameSeriesRepository


class GameSeriesRepository(IGameSeriesRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, game_series: GameSeries) -> GameSeries:
        model = GameSeriesModel(
            id =game_series.id,
            title=game_series.title,
            publisher=game_series.publisher,
            description=game_series.description,
        )
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)

    async def get_by_id(self, series_id: UUID) -> Optional[GameSeries]:
        stmt = select(GameSeriesModel).where(GameSeriesModel.id == series_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_name(self, title: str) -> Optional[GameSeries]:
        stmt = select(GameSeriesModel).where(GameSeriesModel.title == title)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_all(self) -> List[GameSeries]:
        stmt = select(GameSeriesModel).order_by(GameSeriesModel.title)
        result = await self._session.execute(stmt)
        models = result.scalar().all()
        return [self._model_to_entity(model) for model in models]

    async def update(self, game_series: GameSeries) -> GameSeries:
        stmt = select(GameSeriesModel).where(GameSeriesModel.id == game_series.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        model.title = game_series.title
        model.publisher = game_series.publisher
        model.description = game_series.description

        await self._session.flush()
        return self._model_to_entity(model)

    async def delete(self, series_id: UUID) -> bool:
        stmt = select(GameSeriesModel).where(GameSeriesModel.id == series_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            return True
        return False

    def _model_to_entity(self, model: GameSeriesModel) -> GameSeries:
        return GameSeries(
            id=model.id,
            title=model.title,
            publisher=model.publisher,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        )