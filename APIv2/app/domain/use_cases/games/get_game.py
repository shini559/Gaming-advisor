from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository


@dataclass
class GetGameRequest:
    game_id: UUID
    user_id: Optional[UUID] = None  # Pour vérifier les permissions


@dataclass
class GetGameResponse:
    game: Optional[Game]
    success: bool
    message: str


class GetGameUseCase:
    def __init__(self, game_repository: IGameRepository):
        self._game_repository = game_repository

    async def execute(self, request: GetGameRequest) -> GetGameResponse:
        try:
            game = await self._game_repository.get_by_id(request.game_id)

            if not game:
                return GetGameResponse(
                    game=None,
                    success=False,
                    message="Game not found"
                )

            # Vérifier les permissions d'accès
            if not game.is_public and request.user_id != game.created_by:
                return GetGameResponse(
                    game=None,
                    success=False,
                    message="Access denied: Game is private"
                )

            return GetGameResponse(
                game=game,
                success=True,
                message="Game found"
            )

        except Exception as e:
            return GetGameResponse(
                game=None,
                success=False,
                message=f"Failed to get game: {str(e)}"
            )