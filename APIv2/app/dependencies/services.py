from app.domain.ports.services.jwt_service import IJWTService
from app.domain.ports.services.password_service import IPasswordService
from app.services.password_service import PasswordService
from app.services.jwt_service import JWTService
from app.services.blob_storage_service import AzureBlobStorageService
from app.services.redis_queue_service import RedisQueueService
from app.services.openai_processing_service import OpenAIProcessingService

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