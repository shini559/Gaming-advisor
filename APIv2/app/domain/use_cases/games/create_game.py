from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.services.blob_storage_service import IBlobStorageService

@dataclass
class CreateGameRequest:
  title: str
  description: Optional[str] = None
  publisher: Optional[str] = None
  series_id: Optional[UUID] = None
  is_expansion: bool = False
  base_game_id: Optional[UUID] = None
  is_public: Optional[bool] = None  # None = auto-détecté selon role user
  created_by: Optional[UUID] = None
  user_is_admin: bool = False  # Nouveau: pour vérifier les privilèges
  avatar_content: Optional[bytes] = None  # Contenu du fichier avatar
  avatar_filename: Optional[str] = None  # Nom du fichier original

@dataclass
class CreateGameResponse:
  game: Game | None
  success: bool
  message: str

class GameAlreadyExistsError(Exception):
  """Raised when trying to create a game that already exists"""
  pass

class CreateGameUseCase:
  def __init__(self, game_repository: IGameRepository, blob_storage_service: IBlobStorageService):
      self._game_repository = game_repository
      self._blob_storage_service = blob_storage_service

  async def execute(self, request: CreateGameRequest) -> CreateGameResponse:

      self._validate_request(request)

      if await self._game_repository.exists_by_title_publisher_and_user(request.title, request.publisher, request.created_by):
          raise GameAlreadyExistsError(f"Game with title '{request.title}', publisher '{request.publisher}' and user ID '{request.created_by}' already exists")

      try:
          # Déterminer is_public et created_by selon les privilèges admin
          is_public, created_by = self._determine_game_ownership(request)
          
          # Générer l'ID du jeu
          game_id = uuid4()
          
          # Gérer l'upload d'avatar si présent
          avatar_url = None
          if request.avatar_content and request.avatar_filename:
              try:
                  # Déterminer le content type
                  content_type = self._get_content_type_from_filename(request.avatar_filename)
                  
                  # Upload vers Azure Blob Storage
                  file_path, blob_url = await self._blob_storage_service.upload_game_avatar(
                      game_id=game_id,
                      file_content=request.avatar_content,
                      filename=request.avatar_filename,
                      content_type=content_type
                  )
                  avatar_url = blob_url
                  
              except Exception as e:
                  return CreateGameResponse(
                      game=None,
                      success=False,
                      message=f"Failed to upload avatar: {str(e)}"
                  )
          
          # Créer l'entité Game avec l'avatar
          game = Game(
              id=game_id,
              title=request.title,
              description=request.description,
              publisher=request.publisher,
              series_id=request.series_id,
              is_expansion=request.is_expansion,
              base_game_id=request.base_game_id,
              is_public=is_public,
              created_by=created_by,
              avatar=avatar_url,  # URL de l'avatar dans Azure Blob
              created_at=datetime.now(timezone.utc),
              updated_at=datetime.now(timezone.utc)
          )

          # Sauvegarder
          created_game = await self._game_repository.create(game)

          return CreateGameResponse(
              game=created_game,
              success=True,
              message="Game created successfully"
          )

      except Exception as e:
          return CreateGameResponse(
              game=None,
              success=False,
              message=f"Failed to create game: {str(e)}"
          )

  def _determine_game_ownership(self, request: CreateGameRequest) -> tuple[bool, Optional[UUID]]:
      """Détermine is_public et created_by selon les privilèges admin"""
      
      # Si l'utilisateur est admin
      if request.user_is_admin:
          # L'admin peut choisir explicitement is_public
          if request.is_public is True:
              # Jeu public : appartient à la plateforme (created_by = None)
              return True, None
          else:
              # Admin crée un jeu privé : lié à son ID
              return False, request.created_by
      else:
          # Utilisateur normal : toujours privé et lié à son ID
          # (La validation is_public=True est faite dans _validate_request)
          return False, request.created_by

  def _validate_request(self, request: CreateGameRequest) -> None:
      """Validate creation request"""
      errors = []

      if not request.title or len(request.title.strip()) < 1:
          errors.append("Title must be at least 1 character long")
      
      # Validation des privilèges admin pour jeux publics
      if request.is_public is True and not request.user_is_admin:
          errors.append("Seuls les administrateurs peuvent créer des jeux publics")
      
      # Validation de l'avatar
      if request.avatar_content and not request.avatar_filename:
          errors.append("Avatar filename is required when avatar content is provided")
      elif request.avatar_filename and not request.avatar_content:
          errors.append("Avatar content is required when avatar filename is provided")

      if errors:
          raise ValueError(f"Validation errors: {', '.join(errors)}")
  
  def _get_content_type_from_filename(self, filename: str) -> str:
      """Détermine le content type à partir de l'extension du fichier"""
      extension = filename.lower().split('.')[-1] if '.' in filename else ''
      
      content_types = {
          'jpg': 'image/jpeg',
          'jpeg': 'image/jpeg',
          'png': 'image/png',
          'gif': 'image/gif',
          'webp': 'image/webp'
      }
      
      return content_types.get(extension, 'application/octet-stream')