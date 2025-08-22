from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository
from app.shared.utils.datetime_utils import utc_now

@dataclass
class CreateGameRequest:
  title: str
  publisher: Optional[str] = None
  series_id: Optional[UUID] = None
  is_expansion: bool = False
  base_game_id: Optional[UUID] = None
  is_public: bool = False
  created_by: Optional[UUID] = None  # None = équipe

@dataclass
class CreateGameResponse:
  game: Game
  success: bool
  message: str

class CreateGameUseCase:
  def __init__(self, game_repository: IGameRepository):
      self._game_repository = game_repository

  async def execute(self, request: CreateGameRequest) -> CreateGameResponse:
      try:
          # Créer l'entité Game
          game = Game(
              id=uuid4(),
              title=request.title,
              publisher=request.publisher,
              series_id=request.series_id,
              is_expansion=request.is_expansion,
              base_game_id=request.base_game_id,
              is_public=request.is_public,
              created_by=request.created_by,
              created_at=utc_now(),
              updated_at=utc_now()
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