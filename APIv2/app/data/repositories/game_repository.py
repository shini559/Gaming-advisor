from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ClauseElement, ColumnElement

from app.data.models import GameModel
from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository


class GameRepository(IGameRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, game: Game) -> Game:
        model = GameModel(
            id=game.id,
            title=game.title,
            description=game.description,
            publisher=game.publisher,
            series_id=game.series_id,
            is_expansion=game.is_expansion,
            base_game_id=game.base_game_id,
            is_public=game.is_public,
            created_by=game.created_by,
            avatar=game.avatar
        )
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)

    async def get_by_id(self, game_id: UUID) -> Optional[Game]:
        stmt = select(GameModel).where(GameModel.id == game_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_public_games(self) -> List[Game]:
        stmt = select(GameModel).where(GameModel.is_public == True)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return[self._model_to_entity(model) for model in models]

    async def get_user_games(self, user_id: UUID) -> List[Game]:
        stmt = select(GameModel).where(GameModel.created_by == user_id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_available_games_for_user(self, user_id: UUID) -> List[Game]:
        stmt = select(GameModel).where(
            or_(
                GameModel.is_public == True,
                GameModel.created_by == user_id
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_accessible_games_for_user(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[Game]:
        """Get public games + user's private games with pagination"""
        stmt = select(GameModel).where(
            or_(
                GameModel.is_public == True,
                GameModel.created_by == user_id
            )
        ).order_by(GameModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def count_accessible_games_for_user(self, user_id: UUID) -> int:
        """Count accessible games for user (for pagination)"""
        stmt = select(func.count(GameModel.id)).where(
            or_(
                GameModel.is_public == True,
                GameModel.created_by == user_id
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_user_games_paginated(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[Game]:
        """Get user's own games with pagination"""
        stmt = select(GameModel).where(
            GameModel.created_by == user_id
        ).order_by(GameModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def count_user_games(self, user_id: UUID) -> int:
        """Count user's own games (for pagination)"""
        stmt = select(func.count(GameModel.id)).where(
            GameModel.created_by == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_by_series(self, series_id: UUID) -> List[Game]:
        stmt = select(GameModel).where(GameModel.series_id == series_id).order_by(GameModel.title)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_expansions(self, base_game_id: UUID) -> List[Game]:
        stmt = select(GameModel).where(
            GameModel.is_expansion == True,
            GameModel.base_game_id == base_game_id
        ).order_by(GameModel.title)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def exists_by_title_publisher_and_user(self, title: str, publisher: Optional[str], created_by: Optional[UUID]) -> bool:
        """Check if game exists with given title publisher and user"""
        conditions: list[ColumnElement[bool]] = [GameModel.title.ilike(title)]

        if publisher:
            conditions.append(GameModel.publisher.ilike(publisher))
        else:
            conditions.append(GameModel.publisher.is_(None))

        if created_by:
            conditions.append(GameModel.created_by == created_by)
        else:
            conditions.append(GameModel.created_by.is_(None))

        stmt = select(GameModel.id).where(*conditions)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update(self, game: Game) -> Game:
        stmt = select(GameModel).where(GameModel.id == game.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        model.title = game.title
        model.publisher = game.publisher
        model.description = game.description
        model.series_id = game.series_id
        model.is_expansion = game.is_expansion
        model.base_game_id = game.base_game_id
        model.is_public = game.is_public
        model.avatar = game.avatar

        await self._session.flush()
        return self._model_to_entity(model)

    async def delete(self, game_id: UUID) -> bool:
        stmt = select(GameModel).where(GameModel.id == game_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            return True
        return False

    def _model_to_entity(self, model: GameModel) -> Game:
        return Game(
            id=model.id,
            title=model.title,
            publisher=model.publisher,
            description=model.description,
            series_id=model.series_id,
            is_expansion=model.is_expansion,
            base_game_id=model.base_game_id,
            is_public=model.is_public,
            created_by=model.created_by,
            avatar=model.avatar,
            created_at=model.created_at,
            updated_at=model.updated_at
        )