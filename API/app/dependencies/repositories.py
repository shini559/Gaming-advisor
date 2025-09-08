from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.user_session_repository import UserSessionRepository
from app.dependencies.database import get_db_session
from app.data.repositories.user_repository import UserRepository
from app.data.repositories.game_repository import GameRepository
from app.data.repositories.game_series_repository import GameSeriesRepository
from app.data.repositories.game_image_repository import GameImageRepository
from app.data.repositories.game_vector_repository import GameVectorRepository
from app.data.repositories.chat_conversation_repository import ChatConversationRepository
from app.data.repositories.chat_message_repository import ChatMessageRepository
from app.data.repositories.chat_feedback_repository import ChatFeedbackRepository

from app.domain.ports.repositories.user_repository import IUserRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.repositories.game_series_repository import IGameSeriesRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository
from app.domain.ports.repositories.chat_feedback_repository import IChatFeedbackRepository


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


def get_game_image_repository(session: AsyncSession = Depends(get_db_session)) -> IGameImageRepository:
    """Dépendance pour le repository des images de jeu"""
    return GameImageRepository(session)


def get_game_vector_repository(session: AsyncSession = Depends(get_db_session)) -> IGameVectorRepository:
    """Dépendance pour le repository des vecteurs de jeu"""
    return GameVectorRepository(session)


def get_chat_conversation_repository(session: AsyncSession = Depends(get_db_session)) -> IChatConversationRepository:
    """Dépendance pour le repository des conversations de chat"""
    return ChatConversationRepository(session)


def get_chat_message_repository(session: AsyncSession = Depends(get_db_session)) -> IChatMessageRepository:
    """Dépendance pour le repository des messages de chat"""
    return ChatMessageRepository(session)


def get_chat_feedback_repository(session: AsyncSession = Depends(get_db_session)) -> IChatFeedbackRepository:
    """Dépendance pour le repository des feedbacks de chat"""
    return ChatFeedbackRepository(session)

