from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.repositories.user_session_repository import UserSessionRepository
from app.dependencies.database import get_db_session
from app.adapters.database.repositories.user_repository import UserRepository
from app.adapters.database.repositories.game_repository import GameRepository
from app.adapters.database.repositories.game_series_repository import GameSeriesRepository
from app.adapters.database.repositories.game_image_repository import GameImageRepository
from app.adapters.database.repositories.game_vector_repository import GameVectorRepository

from app.domain.ports.repositories.user_repository import IUserRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.repositories.game_series_repository import IGameSeriesRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository


def get_user_session_repository(
        db_session: AsyncSession = Depends(get_db_session)
) -> IUserSessionRepository:
    """Factory pour UserSessionRepository"""
    return UserSessionRepository(db_session)

def get_user_repository(
        session: AsyncSession = Depends(get_db_session)
) -> IUserRepository:
    return UserRepository(session)


def get_game_repository(
        session: AsyncSession = Depends(get_db_session)
) -> IGameRepository:
    return GameRepository(session)


def get_game_series_repository(
        session: AsyncSession = Depends(get_db_session)
) -> IGameSeriesRepository:
    return GameSeriesRepository(session)


def get_game_image_repository(
        session: AsyncSession = Depends(get_db_session)
) -> IGameImageRepository:
    return GameImageRepository(session)


def get_game_vector_repository(
        session: AsyncSession = Depends(get_db_session)
) -> IGameVectorRepository:
    return GameVectorRepository(session)
