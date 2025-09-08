from dataclasses import dataclass
from typing import List
from uuid import UUID

from app.domain.entities.game import Game
from app.domain.ports.repositories.game_repository import IGameRepository


@dataclass
class ListUserGamesRequest:
    """Request pour lister les jeux d'un utilisateur"""
    user_id: UUID
    limit: int = 50
    offset: int = 0


@dataclass 
class ListUserGamesResponse:
    """Response avec la liste des jeux de l'utilisateur"""
    games: List[Game]
    total_count: int
    success: bool
    message: str


class ListUserGamesUseCase:
    """Use case pour lister les jeux créés par un utilisateur spécifique"""

    def __init__(self, game_repository: IGameRepository):
        self._game_repository = game_repository

    async def execute(self, request: ListUserGamesRequest) -> ListUserGamesResponse:
        """
        Récupère les jeux créés par l'utilisateur :
        - Seulement les jeux créés par l'utilisateur (created_by=user_id)
        - Peu importe le statut public/privé
        """
        try:
            # Récupérer les jeux de l'utilisateur
            games = await self._game_repository.get_user_games_paginated(
                user_id=request.user_id,
                limit=request.limit,
                offset=request.offset
            )

            # Compter le total (pour la pagination)
            total_count = await self._game_repository.count_user_games(
                user_id=request.user_id
            )

            return ListUserGamesResponse(
                games=games,
                total_count=total_count,
                success=True,
                message=f"Found {len(games)} user games"
            )

        except Exception as e:
            return ListUserGamesResponse(
                games=[],
                total_count=0,
                success=False,
                message=f"Failed to retrieve user games: {str(e)}"
            )