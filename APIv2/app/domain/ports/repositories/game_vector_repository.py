from abc import abstractmethod, ABC
from typing import Optional, List
from uuid import UUID

from app.domain.entities.game_vector import GameVector


class IGameVectorRepository(ABC):
    @abstractmethod
    async def create(self, vector: GameVector) -> GameVector:
        pass

    @abstractmethod
    async def get_by_id(self, vector_id: UUID) -> Optional[GameVector]:
        pass

    @abstractmethod
    async def get_by_game(self, game_id: UUID) -> List[GameVector]:
        pass

    @abstractmethod
    async def get_by_image(self, image_id: UUID) -> List[GameVector]:
        pass

    @abstractmethod
    async def update(self, vector: GameVector) -> GameVector:
        pass

    @abstractmethod
    async def delete(self, vector_id: UUID) -> bool:
        pass