from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.adapters.auth.jwt_service import JWTService
from app.adapters.database.connection import get_async_session
from app.adapters.database.repositories.user_repository import UserRepository
from app.domain.entities.user import User

# OAuth2 scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Initialize JWT service
        jwt_service = JWTService()
        
        # Get user ID from token
        user_id = jwt_service.get_user_id_from_token(token)
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user_repository = UserRepository(db)
        user = await user_repository.find_by_id(user_id)
        
        if user is None:
            raise credentials_exception
        
        # Check if user is still active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user
    (Alias for get_current_user since we already check is_active)
    """
    return current_user


async def get_current_subscribed_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current user with active subscription
    """
    if not current_user.is_subscribed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires an active subscription"
        )
    return current_user


def require_credits(min_credits: int = 1):
    """
    Dependency factory to require minimum credits
    """
    async def _require_credits(current_user: User = Depends(get_current_user)) -> User:
        if current_user.credits < min_credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Required: {min_credits}, Available: {current_user.credits}"
            )
        return current_user
    
    return _require_credits