from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class GameImage:
    id: UUID
    game_id: UUID
    file_path: str
    original_filename: str | None
    file_size: int
    uploaded_by: UUID
    created_at: datetime