from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class GameVector:
    id: UUID
    game_id: UUID
    image_id: UUID
    vector_embedding: list[float]
    extracted_text: str | None
    page_number: int | None
    created_at: datetime