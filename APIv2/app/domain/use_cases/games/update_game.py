from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository

@dataclass
class UpdateGameRequest:
    game_id: UUID
    user_id: UUID # Pour vérifier les permissions
    title: Optional[str] = None
    description: Optional[str] = None
    publisher: Optional[str] = None
    series_id: Optional[UUID] = None
    is_expansion: Optional[bool] = None
    base_game_id: Optional[UUID] = None
    is_public: Optional[bool] = None

@dataclass
class UpdateGameResponse:
  game: Optional[Game]
  success: bool
  message: str

class UpdateGameUseCase:
  def __init__(self, game_repository: IGameRepository):
      self._game_repository = game_repository

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

          # Vérifier les permissions (seul le créateur peut modifier)
          if game.created_by != request.user_id:
              return UpdateGameResponse(
                  game=None,
                  success=False,
                  message="Permission denied: You can only update your own games"
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
              created_by=game.created_by,  # Jamais modifié
              created_at=game.created_at,  # Jamais modifié
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