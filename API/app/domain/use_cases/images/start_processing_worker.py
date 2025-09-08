from dataclasses import dataclass
from typing import Optional

from app.domain.ports.services.ai_processing_service import IAIProcessingService
from app.domain.ports.services.blob_storage_service import IBlobStorageService
from app.domain.ports.services.queue_service import IQueueService
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository

import asyncio


@dataclass
class StartProcessingWorkerResponse:
  success: bool
  message: str


class StartProcessingWorkerUseCase:
  """Use case pour démarrer le worker de traitement d'images"""

  def __init__(
      self,
      queue_service: IQueueService,
      blob_service: IBlobStorageService,
      ai_service: IAIProcessingService,
      image_repository: Optional[IGameImageRepository],
      vector_repository: Optional[IGameVectorRepository]
  ):
      self._queue_service = queue_service
      self._blob_service = blob_service
      self._ai_service = ai_service
      self._image_repository = image_repository
      self._vector_repository = vector_repository
      self._worker = None

  async def execute(self) -> StartProcessingWorkerResponse:
      """Démarre le worker de traitement d'images"""
      try:
          # Importer ici pour éviter les dépendances circulaires
          from app.services.image_processing_worker import ImageProcessingWorker

          # Créer le worker avec les dépendances injectées
          self._worker = ImageProcessingWorker(
              queue_service=self._queue_service,
              blob_service=self._blob_service,
              ai_service=self._ai_service,
              image_repository=self._image_repository,
              vector_repository=self._vector_repository
          )

          # Démarrer le worker en arrière-plan
          asyncio.create_task(self._worker.start())

          return StartProcessingWorkerResponse(
              success=True,
              message="Image processing worker started successfully"
          )

      except Exception as e:
          return StartProcessingWorkerResponse(
              success=False,
              message=f"Failed to start worker: {str(e)}"
          )

  async def stop(self) -> None:
      """Arrête proprement le worker"""
      if self._worker:
          await self._worker.stop()

  async def _validate_configuration(self) -> Optional[str]:
      """Valide que toutes les configurations nécessaires sont présentes"""

      # Test connexion IA via l'interface injectée
      try:
          ai_success, ai_message = await self._ai_service.test_connection()
          if not ai_success:
              return f"AI service validation failed: {ai_message}"
      except Exception as e:
          return f"AI service test failed: {str(e)}"

      # Test connexion Queue via l'interface injectée
      try:
          # Tenter une opération simple pour valider Redis
          test_status = await self._queue_service.get_job_status("test-validation")
          # Si ça ne plante pas, Redis fonctionne (même si le job n'existe pas)
      except Exception as e:
          return f"Queue service validation failed: {str(e)}"

      # Test connexion Blob Storage via l'interface injectée
      # (Pas de test direct car pas de méthode test, mais ça se validera au premier usage)

      return None  # Aucune erreur