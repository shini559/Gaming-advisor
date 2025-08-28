from fastapi import Depends

from app.dependencies.repositories import (
  get_user_repository, get_game_repository, get_game_series_repository,
  get_game_image_repository, get_user_session_repository,
  get_chat_conversation_repository, get_chat_message_repository, get_chat_feedback_repository
)
from app.dependencies.services import get_password_service, get_jwt_service, get_game_rules_agent
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
from app.domain.use_cases.games.list_user_accessible_games import ListUserAccessibleGamesUseCase
from app.domain.use_cases.games.list_user_games import ListUserGamesUseCase
from app.domain.use_cases.chat.create_conversation import CreateConversationUseCase
from app.domain.use_cases.chat.send_message import SendMessageUseCase
from app.domain.use_cases.chat.get_conversation_history import GetConversationHistoryUseCase
from app.domain.use_cases.chat.add_message_feedback import AddMessageFeedbackUseCase

from app.domain.ports.repositories.user_repository import IUserRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.repositories.game_series_repository import IGameSeriesRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository
from app.domain.ports.repositories.chat_feedback_repository import IChatFeedbackRepository
from app.domain.ports.services.game_rules_agent import IGameRulesAgent


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


def get_list_user_accessible_games_use_case(
  game_repo: IGameRepository = Depends(get_game_repository)
) -> ListUserAccessibleGamesUseCase:
  return ListUserAccessibleGamesUseCase(game_repo)


def get_list_user_games_use_case(
  game_repo: IGameRepository = Depends(get_game_repository)
) -> ListUserGamesUseCase:
  return ListUserGamesUseCase(game_repo)


# Chat Use Cases
def get_create_conversation_use_case(
  conversation_repo: IChatConversationRepository = Depends(get_chat_conversation_repository),
  game_repo: IGameRepository = Depends(get_game_repository)
) -> CreateConversationUseCase:
  """Factory pour CreateConversationUseCase"""
  return CreateConversationUseCase(conversation_repo, game_repo)


def get_send_message_use_case(
  conversation_repo: IChatConversationRepository = Depends(get_chat_conversation_repository),
  message_repo: IChatMessageRepository = Depends(get_chat_message_repository),
  agent: IGameRulesAgent = Depends(get_game_rules_agent)
) -> SendMessageUseCase:
  """Factory pour SendMessageUseCase"""
  return SendMessageUseCase(conversation_repo, message_repo, agent)


def get_conversation_history_use_case(
  conversation_repo: IChatConversationRepository = Depends(get_chat_conversation_repository),
  message_repo: IChatMessageRepository = Depends(get_chat_message_repository)
) -> GetConversationHistoryUseCase:
  """Factory pour GetConversationHistoryUseCase"""
  return GetConversationHistoryUseCase(conversation_repo, message_repo)


def get_add_message_feedback_use_case(
  message_repo: IChatMessageRepository = Depends(get_chat_message_repository),
  conversation_repo: IChatConversationRepository = Depends(get_chat_conversation_repository),
  feedback_repo: IChatFeedbackRepository = Depends(get_chat_feedback_repository)
) -> AddMessageFeedbackUseCase:
  """Factory pour AddMessageFeedbackUseCase"""
  return AddMessageFeedbackUseCase(message_repo, conversation_repo, feedback_repo)