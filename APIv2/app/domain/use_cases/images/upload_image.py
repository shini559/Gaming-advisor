from dataclasses import dataclass
from typing import BinaryIO, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.domain.entities.game_image import GameImage, ImageProcessingStatus
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.services.blob_storage_service import IBlobStorageService
from app.domain.ports.services.queue_service import IQueueService, ProcessingJob


@dataclass
class UploadImageRequest:
  """Request pour l'upload d'une image de jeu"""
  game_id: UUID
  file_content: BinaryIO
  filename: str
  content_type: str
  file_size: int
  uploaded_by: UUID


@dataclass
class UploadImageResponse:
  """Response pour l'upload d'une image"""
  image_id: UUID
  job_id: str
  status: str
  message: str
  blob_url: str
  success: bool


class GameNotFoundError(Exception):
  """Levée quand le jeu n'existe pas"""
  pass


class InvalidFileError(Exception):
  """Levée quand le fichier est invalide"""
  pass


class UploadImageUseCase:
  """Use case pour uploader une image de jeu et lancer le traitement asynchrone"""

  def __init__(
      self,
      game_repository: IGameRepository,
      image_repository: IGameImageRepository,
      blob_service: IBlobStorageService,
      queue_service: IQueueService
  ):
      self._game_repository = game_repository
      self._image_repository = image_repository
      self._blob_service = blob_service
      self._queue_service = queue_service

  async def execute(self, request: UploadImageRequest) -> UploadImageResponse:
      """Exécute l'upload d'image avec traitement asynchrone"""

      try:
          # 1. Valider la requête
          await self._validate_request(request)

          # 2. Vérifier que le jeu existe
          game = await self._game_repository.get_by_id(request.game_id)
          if not game:
              raise GameNotFoundError(f"Game with ID {request.game_id} not found")

          # 3. Créer l'ID de l'image
          image_id = uuid4()

          # 4. Upload vers Azure Blob Storage
          file_path, blob_url = await self._blob_service.upload_image(
              game_id=request.game_id,
              image_id=image_id,
              file_content=request.file_content,
              filename=request.filename,
              content_type=request.content_type
          )

          # 5. Créer l'entité GameImage
          image = GameImage(
              id=image_id,
              game_id=request.game_id,
              file_path=file_path,
              blob_url=blob_url,
              original_filename=request.filename,
              file_size=request.file_size,
              uploaded_by=request.uploaded_by,
              processing_status=ImageProcessingStatus.UPLOADED,
              processing_error=None,
              retry_count=0,
              created_at=datetime.now(timezone.utc),
              processing_started_at=None,
              processing_completed_at=None
          )

          # 6. Sauvegarder en base
          saved_image = await self._image_repository.create(image)

          # 7. Créer la tâche de traitement
          job = ProcessingJob(
              job_id=str(uuid4()),
              image_id=image_id,
              game_id=request.game_id,
              blob_path=file_path,
              filename=request.filename,
              retry_count=0,
              max_retries=3,
              metadata={
                  "content_type": request.content_type,
                  "uploaded_by": str(request.uploaded_by)
              }
          )

          # 8. Ajouter à la queue de traitement
          job_id = await self._queue_service.enqueue_image_processing(job)

          return UploadImageResponse(
              image_id=image_id,
              job_id=job_id,
              status="uploaded",
              message="Image uploaded successfully, processing queued",
              blob_url=blob_url,
              success=True
          )

      except (GameNotFoundError, InvalidFileError) as e:
          return UploadImageResponse(
              image_id=UUID('00000000-0000-0000-0000-000000000000'),
              job_id="",
              status="error",
              message=str(e),
              blob_url="",
              success=False
          )
      except Exception as e:
          return UploadImageResponse(
              image_id=UUID('00000000-0000-0000-0000-000000000000'),
              job_id="",
              status="error",
              message=f"Upload failed: {str(e)}",
              blob_url="",
              success=False
          )

  async def _validate_request(self, request: UploadImageRequest) -> None:
      """Valide la requête d'upload"""
      from app.config import settings

      errors = []

      # Vérifier la taille du fichier
      max_size = settings.image_max_file_size_mb * 1024 * 1024
      if request.file_size > max_size:
          errors.append(f"File size ({request.file_size} bytes) exceeds maximum ({max_size} bytes)")

      # Vérifier le format
      file_extension = request.filename.lower().split('.')[-1] if '.' in request.filename else ''
      if file_extension not in settings.image_allowed_formats:
          errors.append(f"File format '{file_extension}' not allowed. Allowed: {settings.image_allowed_formats}")

      # Vérifier le content-type
      allowed_content_types = [
          'image/jpeg', 'image/jpg', 'image/png'
      ]
      if request.content_type not in allowed_content_types:
          errors.append(f"Content type '{request.content_type}' not allowed")

      if errors:
          raise InvalidFileError(f"File validation failed: {'; '.join(errors)}")
