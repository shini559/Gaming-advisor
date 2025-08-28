from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.entities.game import Game


class IGameRepository(ABC):
    @abstractmethod
    async def create(self, game: Game) -> Game:
        pass

    @abstractmethod
    async def get_by_id(self, game_id: UUID) -> Optional[Game]:
        pass

    @abstractmethod
    async def get_public_games(self) -> List[Game]:
        pass

    @abstractmethod
    async def get_user_games(self, user_id: UUID) -> List[Game]:
        pass

    @abstractmethod
    async def get_available_games_for_user(self, user_id: UUID) -> List[Game]:
        """Get public games + user's private games"""
        pass

    @abstractmethod
    async def get_by_series(self, series_id: UUID) -> List[Game]:
        pass

    @abstractmethod
    async def get_expansions(self, base_game_id: UUID) -> List[Game]:
        pass

    @abstractmethod
    async def update(self, game: Game) -> Game:
        pass

    @abstractmethod
    async def delete(self, game_id: UUID) -> bool:
        pass

    @abstractmethod
    async def exists_by_title_publisher_and_user(self, title: str, publisher: Optional[str], created_by: Optional[UUID]) -> bool:
        pass
