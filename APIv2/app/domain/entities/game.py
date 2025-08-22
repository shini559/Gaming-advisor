from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Game:
    id: UUID
    title: str
    description: str | None
    publisher: str | None
    series_id: UUID | None
    is_expansion: bool
    base_game_id: UUID | None
    is_public: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime