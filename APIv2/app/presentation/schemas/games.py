from uuid import UUID
from typing import List

from pydantic import BaseModel, Field, ConfigDict


class GameCreationRequest(BaseModel):
    """Schema pour la requête d'ajout de jeu'"""
    title: str = Field(..., min_length=1, max_length=100, description="Game title (1-100 characters)")
    publisher: str | None = Field(None, max_length=100, description="Game publisher (optional)")
    description: str | None = Field(None, max_length=10000, description="Game description (optional)")
    series_id: UUID | None = Field(None, description="Game series ID (optional)")
    is_expansion: bool = Field(False, description="Is expansion ? (optional)")
    base_game_id: UUID | None = Field(None, description="Game base ID (optional)")
    is_public: bool | None = Field(None, description="Is game public? (admin only)")
    # created_by est géré côté serveur pour la sécurité

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "title": "Zombicide",
                "publisher": "CMON",
                "description": "A zombie massacre game"
            }
        }
    )

class GameResponse(BaseModel):
    """Schema pour la réponse de jeu"""
    game_id: UUID = Field(..., description="User unique identifier")
    title: str = Field(..., min_length=1, max_length=100, description="Game title (1-100 characters)")
    publisher: str | None = Field(None, max_length=100, description="Game publisher (optional)")
    description: str | None = Field(None, max_length=10000, description="Game description (optional)")
    series_id: UUID | None = Field(None, description="Game series ID (optional)")
    is_expansion: bool = Field(False, description="Is expansion ? (optional)")
    base_game_id: UUID | None = Field(None, description="Game base ID (optional)")
    is_public: bool = Field(..., description="Is public ?")
    created_by: UUID | None = Field(None, description="Created by user ID (optional)")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "title": "Zombicide",
                "publisher": "CMON",
                "description": "A zombie massacre game",
                "series_id": 1,
                "is_expansion": False,
                "base_game_id": 1,
                "is_public": True,
                "created_by": 1
            }
        }
    )


class GamesListResponse(BaseModel):
    """Schema pour la réponse de liste de jeux avec pagination"""
    games: List[GameResponse] = Field(..., description="List of accessible games")
    total_count: int = Field(..., description="Total number of accessible games")
    limit: int = Field(..., description="Number of games per page")
    offset: int = Field(..., description="Number of games skipped")
    has_more: bool = Field(..., description="Whether there are more games to load")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "games": [
                    {
                        "game_id": "uuid-here",
                        "title": "Zombicide",
                        "publisher": "CMON",
                        "description": "A zombie massacre game",
                        "is_public": True,
                        "created_by": "user-uuid"
                    }
                ],
                "total_count": 15,
                "limit": 10,
                "offset": 0,
                "has_more": True
            }
        }
    )