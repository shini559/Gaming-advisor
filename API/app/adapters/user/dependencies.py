from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.connection import get_db
from app.domain.repositories.user_repository import UserRepository
from .repository import PostgreSQLUserRepository


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency injection pour le UserRepository"""
    return PostgreSQLUserRepository(session)