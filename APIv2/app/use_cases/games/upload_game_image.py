from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from app.domain.entities.game_image import GameImage
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.shared.utils.datetime_utils import utc_now

@dataclass
class UploadGameImageRequest:
  game_id: UUID
  file_path: str
  original_filename: Optional[str]
  file_size: int
  uploaded_by: UUID

@dataclass
class UploadGameImageResponse:
  image: Optional[GameImage]
  success: bool
  message: str

class UploadGameImageUseCase:
  def __init__(
      self,
      image_repository: IGameImageRepository,
      game_repository: IGameRepository
  ):
      self._image_repository = image_repository
      self._game_repository = game_repository

  async def execute(self, request: UploadGameImageRequest) -> UploadGameImageResponse:
      try:
          # Vérifier que le jeu existe
          game = await self._game_repository.get_by_id(request.game_id)
          if not game:
              return UploadGameImageResponse(
                  image=None,
                  success=False,
                  message="Game not found"
              )

          # Vérifier les permissions d'upload
          if not game.is_public and game.created_by != request.uploaded_by:
              return UploadGameImageResponse(
                  image=None,
                  success=False,
                  message="Permission denied: Cannot upload to private game"
              )

          # Créer l'image
          image = GameImage(
              id=uuid4(),
              game_id=request.game_id,
              file_path=request.file_path,
              original_filename=request.original_filename,
              file_size=request.file_size,
              uploaded_by=request.uploaded_by,
              created_at=utc_now()
          )

          # Sauvegarder
          created_image = await self._image_repository.create(image)

          return UploadGameImageResponse(
              image=created_image,
              success=True,
              message="Image uploaded successfully"
          )

      except Exception as e:
          return UploadGameImageResponse(
              image=None,
              success=False,
              message=f"Failed to upload image: {str(e)}"
          )