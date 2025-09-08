from fastapi import Depends

from app.dependencies.repositories import (
  get_game_repository,
  get_game_image_repository,
  get_game_vector_repository
)
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository
from app.domain.ports.services.ai_processing_service import IAIProcessingService
from app.domain.ports.services.blob_storage_service import IBlobStorageService
from app.domain.ports.services.queue_service import IQueueService
from app.domain.use_cases.images.start_processing_worker import StartProcessingWorkerUseCase
from app.dependencies.services import get_blob_storage_service, get_queue_service, get_ai_processing_service

def get_start_processing_worker_use_case(
      game_repository: IGameRepository=Depends(get_game_repository),
      image_repository: IGameImageRepository=Depends(get_game_image_repository),
      vector_repository: IGameVectorRepository=Depends(get_game_vector_repository),
      blob_service: IBlobStorageService=Depends(get_blob_storage_service),
      queue_service: IQueueService=Depends(get_queue_service),
      ai_service: IAIProcessingService=Depends(get_ai_processing_service)
) -> StartProcessingWorkerUseCase:
  """Dépendance pour le use case de démarrage du worker"""
  return StartProcessingWorkerUseCase(
      queue_service=queue_service,
      blob_service=blob_service,
      ai_service=ai_service,
      image_repository=image_repository,
      vector_repository=vector_repository
  )