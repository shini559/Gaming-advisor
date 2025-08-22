from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.dependencies.repositories import get_user_repository, get_user_session_repository
from app.dependencies.services import get_jwt_service
from app.domain.entities.user import User
from app.domain.ports.repositories.user_repository import IUserRepository
from app.adapters.auth.jwt_service import JWTService
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository

security = HTTPBearer()

async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  user_repo: IUserRepository = Depends(get_user_repository),
  session_repo: IUserSessionRepository = Depends(get_user_session_repository),
  jwt_service: JWTService = Depends(get_jwt_service)
) -> User:
  """Dependency to get current authenticated user from JWT token"""
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Could not validate credentials",
      headers={"WWW-Authenticate": "Bearer"},
  )

  try:
      token = credentials.credentials
      user_id = jwt_service.get_user_id_from_token(token)
      if user_id is None:
          raise credentials_exception

      user = await user_repo.find_by_id(user_id)
      if user is None:
          raise credentials_exception

      if not user.is_active:
          raise HTTPException(
              status_code=status.HTTP_403_FORBIDDEN,
              detail="User account is deactivated"
          )

      active_sessions_count = await session_repo.count_active_sessions_for_user(user_id)
      if active_sessions_count == 0:
          raise credentials_exception

      return user

  except HTTPException:
      raise
  except Exception:
      raise credentials_exception

async def get_current_active_user(
  current_user: User = Depends(get_current_user)
) -> User:
  return current_user

async def get_current_subscribed_user(
  current_user: User = Depends(get_current_user)
) -> User:
  if not current_user.is_subscribed:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="This feature requires an active subscription"
      )
  return current_user

def require_credits(min_credits: int = 1):
  async def _require_credits(current_user: User = Depends(get_current_user)) -> User:
      if current_user.credits < min_credits:
          raise HTTPException(
              status_code=status.HTTP_402_PAYMENT_REQUIRED,
              detail=f"Insufficient credits. Required: {min_credits}, Available: {current_user.credits}"
          )
      return current_user
  return _require_credits