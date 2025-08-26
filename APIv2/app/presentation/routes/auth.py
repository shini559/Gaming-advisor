from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from app.presentation.schemas.auth import (
    UserRegistrationRequest, UserResponse, TokenResponse,
    RefreshTokenRequest, LogoutRequest, LogoutResponse, UserSessionResponse, ErrorResponse
)
from app.shared.utils.session_utils import generate_session_identifier
from app.domain.use_cases.auth.register_user import RegisterUser, RegisterUserRequest, UserAlreadyExistsError
from app.domain.use_cases.auth.authenticate_user import (
  AuthenticateUser, AuthenticateUserRequest, InvalidCredentialsError, UserNotActiveError
)
from app.domain.use_cases.auth.refresh_token import (
  RefreshToken, RefreshTokenRequest as RefreshTokenUseCase,
  InvalidRefreshTokenError, ExpiredRefreshTokenError
)
from app.domain.use_cases.auth.logout_user import (
  LogoutUser, LogoutUserRequest as LogoutUserUseCase
)
from app.dependencies import (
  get_register_user_use_case,
  get_authenticate_user_use_case,
  get_refresh_token_use_case,
  get_logout_user_use_case,
  get_user_session_repository,
  get_current_user
)
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
  "/register",
  response_model=UserResponse,
  status_code=status.HTTP_201_CREATED,
  responses={
      400: {"model": ErrorResponse, "description": "Validation error"},
      409: {"model": ErrorResponse, "description": "User already exists"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="Register a new user",
  description="Create a new user account with username, email, and password"
)
async def register_user(
  request: UserRegistrationRequest,
  use_case: RegisterUser = Depends(get_register_user_use_case)
) -> UserResponse:
  """Inscrire un nouvel utilisateur"""
  try:
      # Convertir le schéma API en requête use case
      use_case_request = RegisterUserRequest(
          username=request.username,
          email=request.email,
          first_name=request.first_name,
          last_name=request.last_name,
          password=request.password,
          avatar=request.avatar
      )

      # Exécuter le use case
      response = await use_case.execute(use_case_request)

      # Convertir la réponse use case en schéma API
      return UserResponse(
          user_id=response.user_id,
          username=response.username,
          email=response.email,
          first_name=response.first_name,
          last_name=response.last_name,
          is_active=response.is_active,
          credits=response.credits,
          avatar=response.avatar
      )

  except ValueError as e:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=str(e)
      )
  except UserAlreadyExistsError as e:
      raise HTTPException(
          status_code=status.HTTP_409_CONFLICT,
          detail=str(e)
      )
  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="An unexpected error occurred during registration"
      )


@router.post(
  "/login",
  response_model=TokenResponse,
  responses={
      400: {"model": ErrorResponse, "description": "Validation error"},
      401: {"model": ErrorResponse, "description": "Invalid credentials"},
      403: {"model": ErrorResponse, "description": "Account deactivated"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="User login",
  description="Authenticate user and return JWT access token + refresh token"
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    use_case: AuthenticateUser = Depends(get_authenticate_user_use_case)
) -> TokenResponse:
  """Connecter un utilisateur et retourner les tokens JWT"""
  try:
      # Convertir les données OAuth2 en requête use case
      use_case_request = AuthenticateUserRequest(
          username_or_email=form_data.username,
          password=form_data.password,
          device_info={
            "device_type": "web",
            "login_method": "oauth2_form",
            "session_id": generate_session_identifier(request),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "")[:200],
            "timestamp": datetime.now(timezone.utc).isoformat(),
          }
      )

      # Exécuter le use case
      response = await use_case.execute(use_case_request)

      # Convertir la réponse use case en schéma API
      return TokenResponse(
          access_token=response.access_token,
          refresh_token=response.refresh_token,
          token_type=response.token_type,
          expires_in=response.expires_in,
          refresh_expires_in=response.refresh_expires_in,
          user_id=response.user_id,
          username=response.username,
          email=response.email
      )

  except ValueError as e:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=str(e)
      )
  except InvalidCredentialsError as e:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail=str(e),
          headers={"WWW-Authenticate": "Bearer"}
      )
  except UserNotActiveError as e:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail=str(e)
      )
  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="An unexpected error occurred during authentication"
      )

@router.post(
  "/refresh",
  response_model=TokenResponse,
  responses={
      400: {"model": ErrorResponse, "description": "Validation error"},
      401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="Refresh access token",
  description="Refresh an expired access token using a valid refresh token"
)
async def refresh_token(
  request: RefreshTokenRequest,
  use_case: RefreshToken = Depends(get_refresh_token_use_case)
) -> TokenResponse:
  """Rafraîchir un token d'accès expiré"""
  try:
      # Convertir le schéma API en requête use case
      use_case_request = RefreshTokenUseCase(
          refresh_token=request.refresh_token,
          device_info=request.device_info
      )

      # Exécuter le use case
      response = await use_case.execute(use_case_request)

      # Convertir la réponse use case en schéma API
      return TokenResponse(
          access_token=response.access_token,
          refresh_token=response.refresh_token,
          token_type=response.token_type,
          expires_in=response.expires_in,
          refresh_expires_in=response.refresh_expires_in,
          user_id=response.user_id,
          username=response.username,
          email=response.email
      )

  except ValueError as e:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=str(e)
      )
  except (InvalidRefreshTokenError, ExpiredRefreshTokenError) as e:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail=str(e),
          headers={"WWW-Authenticate": "Bearer"}
      )
  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="An unexpected error occurred during token refresh"
      )


@router.post(
  "/logout",
  response_model=LogoutResponse,
  responses={
      400: {"model": ErrorResponse, "description": "Validation error"},
      401: {"model": ErrorResponse, "description": "Invalid token"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="User logout",
  description="Logout user by revoking refresh token(s)"
)
async def logout(
  request: LogoutRequest,
  current_user: User = Depends(get_current_user),
  use_case: LogoutUser = Depends(get_logout_user_use_case)
) -> LogoutResponse:
  """Déconnecter un utilisateur"""
  try:
      # Convertir le schéma API en requête use case
      use_case_request = LogoutUserUseCase(
          refresh_token=request.refresh_token,
          session_id=request.session_id,
          logout_all=request.logout_all
      )

      # Exécuter le use case
      response = await use_case.execute(use_case_request, current_user.id)

      # La réponse use case correspond déjà au schéma API
      return LogoutResponse(
          success=response.success,
          sessions_revoked=response.sessions_revoked,
          message=response.message
      )

  except ValueError as e:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=str(e)
      )
  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="An unexpected error occurred during logout"
      )


@router.get(
  "/sessions",
  response_model=List[UserSessionResponse],
  responses={
      401: {"model": ErrorResponse, "description": "Invalid or expired token"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="Get user sessions",
  description="Get all active sessions for the current user"
)
async def get_user_sessions(
  current_user: User = Depends(get_current_user),
  session_repo = Depends(get_user_session_repository)
) -> List[UserSessionResponse]:
  """Obtenir toutes les sessions actives de l'utilisateur"""
  try:
      sessions = await session_repo.find_active_by_user_id(current_user.id)

      return [
          UserSessionResponse(
              session_id=str(session.id),
              device_info=session.device_info,
              created_at=session.created_at.isoformat(),
              last_used_at=session.last_used_at.isoformat(),
              expires_at=session.expires_at.isoformat(),
              is_current=False  # TODO: déterminer la session courante
          )
          for session in sessions
      ]

  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="An unexpected error occurred while fetching sessions"
      )


@router.get(
  "/me",
  response_model=UserResponse,
  responses={
      401: {"model": ErrorResponse, "description": "Invalid or expired token"},
      403: {"model": ErrorResponse, "description": "Account deactivated"}
  },
  summary="Get current user profile",
  description="Get the profile of the currently authenticated user"
)
async def get_current_user_profile(
  current_user: User = Depends(get_current_user)
) -> UserResponse:
  """Obtenir le profil de l'utilisateur authentifié"""
  return UserResponse(
      user_id=str(current_user.id),
      username=current_user.username,
      email=current_user.email,
      first_name=current_user.first_name,
      last_name=current_user.last_name,
      is_active=current_user.is_active,
      credits=current_user.credits,
      avatar=current_user.avatar
  )