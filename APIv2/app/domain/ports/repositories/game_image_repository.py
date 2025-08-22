from abc import abstractmethod, ABC
from typing import List, Optional
from uuid import UUID

from app.domain.entities.game_image import GameImage


class IGameImageRepository(ABC):
    @abstractmethod
    async def create(self, image: GameImage) -> GameImage:
        pass

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> Optional[GameImage]:
        pass

    @abstractmethod
    async def get_by_game(self, game_id: UUID) -> List[GameImage]:
        pass

    @abstractmethod
    async def get_by_uploader(self, user_id: UUID) -> List[GameImage]:
        pass

    @abstractmethod
    async def update(self, image: GameImage) -> GameImage:
        pass

    @abstractmethod
    async def delete(self, image_id: UUID) -> bool:
        pass