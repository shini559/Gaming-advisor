from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.exc import IntegrityError

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from .models import UserModel


class PostgreSQLUserRepository(UserRepository):
    """Implémentation PostgreSQL de UserRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        """Sauvegarde un utilisateur"""
        db_user = UserModel(
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
            is_premium=user.is_premium,
            credits=user.credits,
            avatar_url=user.avatar_url
        )

        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)

        # Conversion Model → Entity
        return self._to_entity(db_user)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par ID"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        return self._to_entity(db_user) if db_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par email"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        db_user = result.scalar_one_or_none()
        return self._to_entity(db_user) if db_user else None

    async def email_exists(self, email: str) -> bool:     
        """Vérifie si un email existe"""
        result = await self.session.execute(
            select(exists().where(UserModel.email == email))
        )
        return result.scalar()

    async def username_exists(self, username: str) -> bool:
        """Vérifie si un username existe"""
        result = await self.session.execute(
            select(exists().where(UserModel.username == username))
        )
        return result.scalar()

    def _to_entity(self, db_user: UserModel) -> User:     
        """Convertit UserModel vers User entity"""        
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            password_hash=db_user.password_hash,
            is_active=db_user.is_active,
            is_premium=db_user.is_premium,
            credits=db_user.credits,
            avatar_url=db_user.avatar_url,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )