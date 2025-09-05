from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Game:
    """A game"""

    id: UUID
    title: str
    description: str | None
    publisher: str | None
    series_id: UUID | None
    is_expansion: bool
    base_game_id: UUID | None
    is_public: bool
    created_by: UUID | None
    avatar: str | None  # URL de l'image d'avatar stockée dans Azure Blob Storage
    created_at: datetime
    updated_at: datetime