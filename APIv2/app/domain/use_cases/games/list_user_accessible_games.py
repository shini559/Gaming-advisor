from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository


@dataclass
class ListUserAccessibleGamesRequest:
    """Request pour lister les jeux accessibles à un utilisateur"""
    user_id: UUID
    limit: int = 50
    offset: int = 0


@dataclass 
class ListUserAccessibleGamesResponse:
    """Response avec la liste des jeux accessibles"""
    games: List[Game]
    total_count: int
    success: bool
    message: str


class ListUserAccessibleGamesUseCase:
    """Use case pour lister les jeux accessibles à un utilisateur"""

    def __init__(self, game_repository: IGameRepository):
        self._game_repository = game_repository

    async def execute(self, request: ListUserAccessibleGamesRequest) -> ListUserAccessibleGamesResponse:
        """
        Récupère les jeux accessibles à un utilisateur :
        - Tous les jeux publics (is_public=True)
        - Les jeux privés créés par l'utilisateur (is_public=False AND created_by=user_id)
        """
        try:
            # Récupérer les jeux accessibles
            games = await self._game_repository.get_accessible_games_for_user(
                user_id=request.user_id,
                limit=request.limit,
                offset=request.offset
            )

            # Compter le total (pour la pagination)
            total_count = await self._game_repository.count_accessible_games_for_user(
                user_id=request.user_id
            )

            return ListUserAccessibleGamesResponse(
                games=games,
                total_count=total_count,
                success=True,
                message=f"Found {len(games)} accessible games"
            )

        except Exception as e:
            return ListUserAccessibleGamesResponse(
                games=[],
                total_count=0,
                success=False,
                message=f"Failed to retrieve accessible games: {str(e)}"
            )