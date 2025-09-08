from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.services.blob_storage_service import IBlobStorageService

@dataclass
class UpdateGameRequest:
    game_id: UUID
    user_id: UUID # Pour vérifier les permissions
    user_is_admin: bool = False  # Privilèges administrateur
    title: Optional[str] = None
    description: Optional[str] = None
    publisher: Optional[str] = None
    series_id: Optional[UUID] = None
    is_expansion: Optional[bool] = None
    base_game_id: Optional[UUID] = None
    is_public: Optional[bool] = None
    avatar_content: Optional[bytes] = None  # Contenu du nouvel avatar
    avatar_filename: Optional[str] = None  # Nom du fichier avatar

@dataclass
class UpdateGameResponse:
  game: Optional[Game]
  success: bool
  message: str

class UpdateGameUseCase:
  def __init__(self, game_repository: IGameRepository, blob_storage_service: IBlobStorageService):
      self._game_repository = game_repository
      self._blob_storage_service = blob_storage_service

  async def execute(self, request: UpdateGameRequest) -> UpdateGameResponse:
      try:
          # Récupérer le jeu existant
          game = await self._game_repository.get_by_id(request.game_id)
          if not game:
              return UpdateGameResponse(
                  game=None,
                  success=False,
                  message="Game not found"
              )

          # Vérifier les permissions 
          # - Le propriétaire peut toujours modifier ses jeux
          # - Les administrateurs peuvent modifier les jeux publics
          can_update = (
              game.created_by == request.user_id or  # Propriétaire
              (request.user_is_admin and game.is_public)  # Admin sur jeu public
          )
          
          if not can_update:
              return UpdateGameResponse(
                  game=None,
                  success=False,
                  message="Permission denied: You can only update your own games or public games (admin only)"
              )

          # Gérer l'upload d'avatar si un nouveau est fourni
          avatar_url = game.avatar  # Par défaut, garder l'avatar existant
          if request.avatar_content and request.avatar_filename:
              try:
                  # Déterminer le content type
                  content_type = self._get_content_type_from_filename(request.avatar_filename)
                  
                  # Upload vers Azure Blob Storage (remplace l'ancien avatar)
                  file_path, blob_url = await self._blob_storage_service.upload_game_avatar(
                      game_id=request.game_id,
                      file_content=request.avatar_content,
                      filename=request.avatar_filename,
                      content_type=content_type
                  )
                  avatar_url = blob_url
                  
              except Exception as e:
                  return UpdateGameResponse(
                      game=None,
                      success=False,
                      message=f"Failed to upload avatar: {str(e)}"
                  )

          # Valider base_game_id si fourni (clé étrangère importante)
          if request.base_game_id is not None:
              # Valider que le jeu de base existe
              base_game = await self._game_repository.get_by_id(request.base_game_id)
              if not base_game:
                  return UpdateGameResponse(
                      game=None,
                      success=False,
                      message=f"Base game with ID {request.base_game_id} does not exist"
                  )

          # Valider les privilèges pour is_public (même logique que CreateGame)
          if request.is_public is True and not request.user_is_admin:
              return UpdateGameResponse(
                  game=None,
                  success=False,
                  message="Permission denied: Only administrators can set games as public"
              )

          # Mettre à jour les champs modifiés
          updated_game = Game(
              id=game.id,
              title=request.title if request.title is not None else game.title,
              description=request.description if request.description is not None else game.description,
              publisher=request.publisher if request.publisher is not None else game.publisher,
              series_id=request.series_id if request.series_id is not None else game.series_id,
              is_expansion=request.is_expansion if request.is_expansion is not None else game.is_expansion,
              base_game_id=request.base_game_id if request.base_game_id is not None else game.base_game_id,
              is_public=request.is_public if request.is_public is not None else game.is_public,
              created_by=game.created_by,
              avatar=avatar_url,  # Nouvel avatar ou avatar existant
              created_at=game.created_at,
              updated_at=datetime.now(timezone.utc)
          )

          # Sauvegarder
          saved_game = await self._game_repository.update(updated_game)

          return UpdateGameResponse(
              game=saved_game,
              success=True,
              message="Game updated successfully"
          )

      except Exception as e:
          return UpdateGameResponse(
              game=None,
              success=False,
              message=f"Failed to update game: {str(e)}"
          )
  
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