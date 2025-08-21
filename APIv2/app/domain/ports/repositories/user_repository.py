from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.user import User


class IUserRepository(ABC):
    """Interface for User repository (Port)"""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Save or update a user"""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """Find user by ID"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email"""
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists with given username"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID. Returns True if deleted."""
        pass