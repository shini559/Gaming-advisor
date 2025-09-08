from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID


@dataclass
class GameVector:
    """
    Vectors extracted from a game image
    """
    id: UUID
    game_id: UUID
    image_id: UUID
    created_at: datetime
    
    # === OCR (Optical Character Recognition) ===
    ocr_content: Optional[str] = None
    ocr_embedding: Optional[List[float]] = None
    
    # === Visual description ===
    description_content: Optional[str] = None  
    description_embedding: Optional[List[float]] = None
    
    # === Labels (structured JSON) ===
    labels_content: Optional[str] = None  # JSON: {"game_elements": [...], "concepts": [...], ...}
    labels_embedding: Optional[List[float]] = None
    
    # === Metadata ===
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None  # Calculated during search
    