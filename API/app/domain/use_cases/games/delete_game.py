from dataclasses import dataclass
from uuid import UUID

from app.domain.ports.repositories.game_repository import IGameRepository

@dataclass
class DeleteGameRequest:
  game_id: UUID
  user_id: UUID  # Pour vérifier les permissions

@dataclass
class DeleteGameResponse:
  success: bool
  message: str

class DeleteGameUseCase:
  def __init__(self, game_repository: IGameRepository):
      self._game_repository = game_repository

  async def execute(self, request: DeleteGameRequest) -> DeleteGameResponse:
      try:
          # Vérifier que le jeu existe et les permissions
          game = await self._game_repository.get_by_id(request.game_id)
          if not game:
              return DeleteGameResponse(
                  success=False,
                  message="Game not found"
              )

          # Vérifier les permissions (seul le créateur peut supprimer)
          if game.created_by != request.user_id:
              return DeleteGameResponse(
                  success=False,
                  message="Permission denied: You can only delete your own games"
              )

          # Supprimer le jeu
          deleted = await self._game_repository.delete(request.game_id)

          if deleted:
              return DeleteGameResponse(
                  success=True,
                  message="Game deleted successfully"
              )
          else:
              return DeleteGameResponse(
                  success=False,
                  message="Failed to delete game"
              )

      except Exception as e:
          return DeleteGameResponse(
              success=False,
              message=f"Failed to delete game: {str(e)}"
          )