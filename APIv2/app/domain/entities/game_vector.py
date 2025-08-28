from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from uuid import UUID


@dataclass
class GameVector:
    """
    Entité représentant un vecteur de données extraites d'une image de jeu
    Architecture 3-paires : chaque type de contenu a son texte + embedding dédié
    """
    id: UUID
    game_id: UUID
    image_id: UUID
    created_at: datetime
    
    # === OCR (Optical Character Recognition) ===
    ocr_content: Optional[str] = None
    ocr_embedding: Optional[List[float]] = None
    
    # === Description visuelle ===
    description_content: Optional[str] = None  
    description_embedding: Optional[List[float]] = None
    
    # === Métadonnées/Labels (JSON structuré) ===
    labels_content: Optional[str] = None  # JSON: {"game_elements": [...], "concepts": [...], ...}
    labels_embedding: Optional[List[float]] = None
    
    # === Métadonnées ===
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None  # Score calculé lors de la recherche
    
    def has_ocr_data(self) -> bool:
        """Vérifie si ce vecteur contient des données OCR"""
        return bool(self.ocr_content and self.ocr_embedding)
    
    def has_description_data(self) -> bool:
        """Vérifie si ce vecteur contient des données de description"""
        return bool(self.description_content and self.description_embedding)
    
    def has_labels_data(self) -> bool:
        """Vérifie si ce vecteur contient des données de labels"""
        return bool(self.labels_content and self.labels_embedding)
    
    def get_content_for_search_type(self, search_type: str) -> Optional[str]:
        """Retourne le contenu approprié selon le type de recherche"""
        if search_type == "ocr":
            return self.ocr_content
        elif search_type == "description":
            return self.description_content
        elif search_type == "labels":
            return self.labels_content
        return None
    
    def get_embedding_for_search_type(self, search_type: str) -> Optional[List[float]]:
        """Retourne l'embedding approprié selon le type de recherche"""
        if search_type == "ocr":
            return self.ocr_embedding
        elif search_type == "description":
            return self.description_embedding
        elif search_type == "labels":
            return self.labels_embedding
        return None