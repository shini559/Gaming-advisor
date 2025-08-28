from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class GameSeries:
    id: UUID
    title: str
    publisher: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime