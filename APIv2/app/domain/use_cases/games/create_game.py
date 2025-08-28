from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository

@dataclass
class CreateGameRequest:
  title: str
  description: Optional[str] = None
  publisher: Optional[str] = None
  series_id: Optional[UUID] = None
  is_expansion: bool = False
  base_game_id: Optional[UUID] = None
  is_public: bool = False
  created_by: Optional[UUID] = None

@dataclass
class CreateGameResponse:
  game: Game | None
  success: bool
  message: str

class GameAlreadyExistsError(Exception):
  """Raised when trying to create a game that already exists"""
  pass

class CreateGameUseCase:
  def __init__(self, game_repository: IGameRepository):
      self._game_repository = game_repository

  async def execute(self, request: CreateGameRequest) -> CreateGameResponse:

      self._validate_request(request)

      if await self._game_repository.exists_by_title_publisher_and_user(request.title, request.publisher, request.created_by):
          raise GameAlreadyExistsError(f"Game with title '{request.title}', publisher '{request.publisher}' and user ID '{request.created_by}' already exists")

      try:
          # Créer l'entité Game
          game = Game(
              id=uuid4(),
              title=request.title,
              description=request.description,
              publisher=request.publisher,
              series_id=request.series_id,
              is_expansion=request.is_expansion,
              base_game_id=request.base_game_id,
              is_public=request.is_public,
              created_by=request.created_by,
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

  def _validate_request(self, request: CreateGameRequest) -> None:
      """Validate creation request"""
      errors = []

      if not request.title or len(request.title.strip()) < 1:
          errors.append("Title must be at least 1 character long")

      # is_public peut être True ou False selon les besoins

      if errors:
          raise ValueError(f"Validation errors: {', '.join(errors)}")