from fastapi import Depends

from app.domain.ports.services.jwt_service import IJWTService
from app.domain.ports.services.password_service import IPasswordService
from app.domain.ports.services.vector_search_service import IVectorSearchService
from app.domain.ports.services.game_rules_agent import IGameRulesAgent
from app.services.password_service import PasswordService
from app.services.jwt_service import JWTService
from app.services.blob_storage_service import AzureBlobStorageService
from app.services.redis_queue_service import RedisQueueService
from app.services.openai_processing_service import OpenAIProcessingService
from app.services.vector_search_service import VectorSearchService
from app.services.game_rules_agent import GameRulesAgent
from app.dependencies.repositories import get_game_vector_repository, get_chat_message_repository, get_game_image_repository
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository

def get_password_service() -> IPasswordService:
  """Factory for PasswordService"""
  return PasswordService()

def get_jwt_service() -> IJWTService:
  """Factory for JWTService"""
  return JWTService()

# Services singletons pour les services Azure et Redis
_blob_service = None
_queue_service = None
_ai_service = None

def get_blob_storage_service() -> AzureBlobStorageService:
  """Dépendance pour le service Azure Blob Storage"""
  global _blob_service
  if _blob_service is None:
      _blob_service = AzureBlobStorageService()
  return _blob_service

def get_queue_service() -> RedisQueueService:
  """Dépendance pour le service de queue Redis"""
  global _queue_service
  if _queue_service is None:
      _queue_service = RedisQueueService()
  return _queue_service

def get_ai_processing_service() -> OpenAIProcessingService:
  """Dépendance pour le service IA OpenAI"""
  global _ai_service
  if _ai_service is None:
      _ai_service = OpenAIProcessingService()
  return _ai_service


# Services IA pour le chat
_vector_search_service = None
_game_rules_agent = None


def get_vector_search_service(
    vector_repository: IGameVectorRepository = Depends(get_game_vector_repository),
    image_repository: IGameImageRepository = Depends(get_game_image_repository)
) -> IVectorSearchService:
    """Dépendance pour le service de recherche vectorielle"""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService(vector_repository, image_repository)
    return _vector_search_service


def get_game_rules_agent(
    vector_search_service: IVectorSearchService = Depends(get_vector_search_service),
    message_repository: IChatMessageRepository = Depends(get_chat_message_repository),
    image_repository: IGameImageRepository = Depends(get_game_image_repository)
) -> IGameRulesAgent:
    """Dépendance pour l'agent IA des règles de jeu"""
    global _game_rules_agent
    if _game_rules_agent is None:
        _game_rules_agent = GameRulesAgent(vector_search_service, message_repository, image_repository)
    return _game_rules_agent