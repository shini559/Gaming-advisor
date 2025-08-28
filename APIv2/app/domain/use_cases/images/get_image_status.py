from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.entities.game_image import GameImage
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.services.queue_service import IQueueService


@dataclass
class GetImageStatusRequest:
  """Request pour récupérer le statut d'une image"""
  image_id: UUID
  user_id: UUID  # Pour vérifier les permissions


@dataclass
class GetImageStatusResponse:
  """Response avec le statut de traitement d'une image"""
  image_id: UUID
  job_id: Optional[str]
  status: str  # uploaded, processing, completed, failed, retrying
  progress: Optional[str]
  error_message: Optional[str]
  created_at: str
  processing_started_at: Optional[str]
  processing_completed_at: Optional[str]
  retry_count: int
  success: bool


class ImageNotFoundError(Exception):
  """Levée quand l'image n'existe pas"""
  pass


class ImageAccessDeniedError(Exception):
  """Levée quand l'utilisateur n'a pas accès à l'image"""
  pass


class GetImageStatusUseCase:
  """Use case pour récupérer le statut de traitement d'une image"""

  def __init__(
      self,
      image_repository: IGameImageRepository,
      queue_service: IQueueService
  ):
      self._image_repository = image_repository
      self._queue_service = queue_service

  async def execute(self, request: GetImageStatusRequest) -> GetImageStatusResponse:
      """Récupère le statut de traitement d'une image"""

      try:
          # 1. Récupérer l'image
          image = await self._image_repository.get_by_id(request.image_id)
          if not image:
              raise ImageNotFoundError(f"Image {request.image_id} not found")

          # 2. Vérifier les permissions
          # L'utilisateur doit être le propriétaire de l'image ou avoir accès au jeu
          if image.uploaded_by != request.user_id:
              # TODO: Vérifier si l'utilisateur a accès au jeu (jeu public ou créateur du jeu)
              # Pour l'instant, on autorise seulement le propriétaire de l'image
              raise ImageAccessDeniedError("Access denied to this image")

          # 3. Récupérer le statut de la queue si disponible
          job_status = None
          job_id = None

          # TODO: Stocker le job_id dans l'image ou récupérer depuis les métadonnées
          # Pour l'instant on simule
          if image.processing_status.value in ["uploaded", "processing"]:
              job_status = image.processing_status.value
              job_id = f"job-{image.id}"

          # 4. Déterminer le progrès
          progress = self._get_progress_message(image)

          return GetImageStatusResponse(
              image_id=image.id,
              job_id=job_id,
              status=image.processing_status.value,
              progress=progress,
              error_message=image.processing_error,
              created_at=image.created_at.isoformat(),
              processing_started_at=image.processing_started_at.isoformat() if image.processing_started_at else None,
              processing_completed_at=image.processing_completed_at.isoformat() if image.processing_completed_at else None,
              retry_count=image.retry_count,
              success=True
          )

      except (ImageNotFoundError, ImageAccessDeniedError) as e:
          return GetImageStatusResponse(
              image_id=request.image_id,
              job_id=None,
              status="error",
              progress=None,
              error_message=str(e),
              created_at="",
              processing_started_at=None,
              processing_completed_at=None,
              retry_count=0,
              success=False
          )
      except Exception as e:
          return GetImageStatusResponse(
              image_id=request.image_id,
              job_id=None,
              status="error",
              progress=None,
              error_message=f"Status check failed: {str(e)}",
              created_at="",
              processing_started_at=None,
              processing_completed_at=None,
              retry_count=0,
              success=False
          )

  def _get_progress_message(self, image: GameImage) -> Optional[str]:
      """Génère un message de progrès basé sur le statut"""
      status = image.processing_status

      if status.value == "uploaded":
          return "Image uploaded, waiting for processing"
      elif status.value == "processing":
          return "AI processing in progress"
      elif status.value == "completed":
          return "Processing completed successfully"
      elif status.value == "failed":
          if image.retry_count > 0:
              return f"Processing failed after {image.retry_count} attempts"
          return "Processing failed"
      elif status.value == "retrying":
          return f"Retrying processing (attempt {image.retry_count + 1})"

      return None