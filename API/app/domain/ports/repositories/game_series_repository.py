from abc import abstractmethod, ABC
from typing import List, Optional
from uuid import UUID

from app.domain.entities.game_series import GameSeries


class IGameSeriesRepository(ABC):
    @abstractmethod
    async def create(selfself, game_series: GameSeries) -> GameSeries:
        pass

    @abstractmethod
    async def get_by_id(self, series_id: UUID) -> Optional[GameSeries]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[GameSeries]:
        pass

    @abstractmethod
    async def get_all(self) -> List[GameSeries]:
        pass

    @abstractmethod
    async def update(self, game_series: GameSeries) -> GameSeries:
        pass

    @abstractmethod
    async def delete(selfself, series_id: UUID) -> bool:
        pass