from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.domain.entities.game_series import GameSeries
from app.domain.ports.repositories.game_series_repository import IGameSeriesRepository
from app.shared.utils.datetime_utils import utc_now

@dataclass
class CreateGameSeriesRequest:
  name: str
  publisher: Optional[str] = None
  description: Optional[str] = None

@dataclass
class CreateGameSeriesResponse:
  series: Optional[GameSeries]
  success: bool
  message: str

class CreateGameSeriesUseCase:
  def __init__(self, series_repository: IGameSeriesRepository):
      self._series_repository = series_repository

  async def execute(self, request: CreateGameSeriesRequest) -> CreateGameSeriesResponse:
      try:
          # Vérifier si une série avec ce nom existe déjà
          existing = await self._series_repository.get_by_name(request.name)
          if existing:
              return CreateGameSeriesResponse(
                  series=None,
                  success=False,
                  message="A series with this name already exists"
              )

          # Créer la série
          series = GameSeries(
              id=uuid4(),
              name=request.name,
              publisher=request.publisher,
              description=request.description,
              created_at=utc_now(),
              updated_at=utc_now()
          )

          # Sauvegarder
          created_series = await self._series_repository.create(series)

          return CreateGameSeriesResponse(
              series=created_series,
              success=True,
              message="Game series created successfully"
          )

      except Exception as e:
          return CreateGameSeriesResponse(
              series=None,
              success=False,
              message=f"Failed to create series: {str(e)}"
          )