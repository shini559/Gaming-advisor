from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository

@dataclass
class ListGamesRequest:
  user_id: Optional[UUID] = None  # None = jeux publics seulement
  series_id: Optional[UUID] = None
  only_user_games: bool = False

@dataclass
class ListGamesResponse:
  games: List[Game]
  success: bool
  message: str

class ListGamesUseCase:
  def __init__(self, game_repository: IGameRepository):
      self._game_repository = game_repository

  async def execute(self, request: ListGamesRequest) -> ListGamesResponse:
      try:
          if request.series_id:
              # Filtrer par série
              games = await self._game_repository.get_by_series(request.series_id)
          elif request.only_user_games and request.user_id:
              # Jeux privés de l'utilisateur uniquement
              games = await self._game_repository.get_user_games(request.user_id)
          elif request.user_id:
              # Jeux accessibles à l'utilisateur (publics + ses privés)
              games = await self._game_repository.get_available_games_for_user(request.user_id)
          else:
              # Jeux publics uniquement
              games = await self._game_repository.get_public_games()

          return ListGamesResponse(
              games=games,
              success=True,
              message=f"Found {len(games)} games"
          )

      except Exception as e:
          return ListGamesResponse(
              games=[],
              success=False,
              message=f"Failed to list games: {str(e)}"
          )