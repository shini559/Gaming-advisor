from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.domain.entities.user import User
from app.domain.ports.repositories.user_repository import IUserRepository
from app.adapters.database.models.user import UserModel


class UserRepository(IUserRepository):
    """SQLAlchemy implementation of IUserRepository"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, user: User) -> User:
        """Save or update a user"""
        # Check if user exists (update) or is new (create)
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Update existing user
            existing_user.username = user.username
            existing_user.email = user.email
            existing_user.first_name = user.first_name
            existing_user.last_name = user.last_name
            existing_user.avatar = user.avatar
            existing_user.hashed_password = user.hashed_password
            existing_user.is_active = user.is_active
            existing_user.is_subscribed = user.is_subscribed
            existing_user.credits = user.credits
            existing_user.updated_at = user.updated_at
            user_model = existing_user
        else:
            # Create new user
            user_model = UserModel(
                id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar=user.avatar,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                is_subscribed=user.is_subscribed,
                credits=user.credits,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            self._session.add(user_model)
        
        try:
            await self._session.commit()
            await self._session.refresh(user_model)
            return self._to_domain(user_model)
        except IntegrityError as e:
            await self._session.rollback()
            raise ValueError(f"User with this email or username already exists: {e}")
    
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """Find user by ID"""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._to_domain(user_model) if user_model else None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        stmt = select(UserModel).where(UserModel.email == email.lower())
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._to_domain(user_model) if user_model else None
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        stmt = select(UserModel).where(UserModel.username == username.lower())
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._to_domain(user_model) if user_model else None
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email"""
        stmt = select(UserModel.id).where(UserModel.email == email.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists with given username"""
        stmt = select(UserModel.id).where(UserModel.username == username.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID. Returns True if deleted."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        if user_model:
            await self._session.delete(user_model)
            await self._session.commit()
            return True
        return False
    
    def _to_domain(self, user_model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity"""
        return User(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            avatar=user_model.avatar,
            hashed_password=user_model.hashed_password,
            is_active=user_model.is_active,
            is_subscribed=user_model.is_subscribed,
            credits=user_model.credits,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at
        )