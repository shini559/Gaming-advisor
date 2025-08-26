from fastapi import Depends

from app.dependencies.repositories import (
  get_user_repository, get_game_repository, get_game_series_repository,
  get_game_image_repository, get_user_session_repository
)
from app.dependencies.services import get_password_service, get_jwt_service
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository
from app.domain.ports.services.jwt_service import IJWTService
from app.domain.ports.services.password_service import IPasswordService
from app.domain.use_cases.auth.logout_user import LogoutUser
from app.domain.use_cases.auth.refresh_token import RefreshToken

# Import use cases
from app.domain.use_cases.auth.register_user import RegisterUser
from app.domain.use_cases.auth.authenticate_user import AuthenticateUser
from app.domain.use_cases.games.create_game import CreateGameUseCase
from app.domain.use_cases.games.get_game import GetGameUseCase
from app.domain.use_cases.games import ListGamesUseCase
from app.domain.use_cases.games.update_game import UpdateGameUseCase
from app.domain.use_cases.games.delete_game import DeleteGameUseCase
from app.domain.use_cases.games.upload_game_image import UploadGameImageUseCase
from app.domain.use_cases.games import CreateGameSeriesUseCase

from app.domain.ports.repositories.user_repository import IUserRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.repositories.game_series_repository import IGameSeriesRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository


# Auth Use Cases
def get_register_user_use_case(
  user_repo: IUserRepository = Depends(get_user_repository),
  password_service: IPasswordService = Depends(get_password_service)
) -> RegisterUser:
  return RegisterUser(user_repo, password_service)


def get_authenticate_user_use_case(
  user_repo: IUserRepository = Depends(get_user_repository),
  session_repo: IUserSessionRepository = Depends(get_user_session_repository),
  password_service: IPasswordService = Depends(get_password_service),
  jwt_service: IJWTService = Depends(get_jwt_service)
) -> AuthenticateUser:
  """Factory pour AuthenticateUser use case"""
  return AuthenticateUser(user_repo, session_repo, password_service, jwt_service)


def get_refresh_token_use_case(
  user_repo: IUserRepository = Depends(get_user_repository),
  session_repo: IUserSessionRepository = Depends(get_user_session_repository),
jwt_service: IJWTService = Depends(get_jwt_service)
) -> RefreshToken:
  """Factory pour RefreshToken use case"""
  return RefreshToken(user_repo, session_repo, jwt_service)


def get_logout_user_use_case(
  session_repo: IUserSessionRepository = Depends(get_user_session_repository),
  jwt_service: IJWTService = Depends(get_jwt_service)
) -> LogoutUser:
  """Factory pour LogoutUser use case"""
  return LogoutUser(session_repo, jwt_service)


# Game Use Cases
def get_create_game_use_case(
  game_repo: IGameRepository = Depends(get_game_repository)
) -> CreateGameUseCase:
  return CreateGameUseCase(game_repo)


def get_get_game_use_case(
  game_repo: IGameRepository = Depends(get_game_repository)
) -> GetGameUseCase:
  return GetGameUseCase(game_repo)


def get_list_games_use_case(
  game_repo: IGameRepository = Depends(get_game_repository)
) -> ListGamesUseCase:
  return ListGamesUseCase(game_repo)


def get_update_game_use_case(
  game_repo: IGameRepository = Depends(get_game_repository)
) -> UpdateGameUseCase:
  return UpdateGameUseCase(game_repo)


def get_delete_game_use_case(
  game_repo: IGameRepository = Depends(get_game_repository)
) -> DeleteGameUseCase:
  return DeleteGameUseCase(game_repo)


def get_upload_game_image_use_case(
  image_repo: IGameImageRepository = Depends(get_game_image_repository),
  game_repo: IGameRepository = Depends(get_game_repository)
) -> UploadGameImageUseCase:
  return UploadGameImageUseCase(image_repo, game_repo)


def get_create_game_series_use_case(
  series_repo: IGameSeriesRepository = Depends(get_game_series_repository)
) -> CreateGameSeriesUseCase:
  return CreateGameSeriesUseCase(series_repo)