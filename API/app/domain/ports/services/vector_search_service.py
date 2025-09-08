from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass
class VectorSearchResult:
    """Résultat d'une recherche vectorielle découplée"""
    
    vector_id: UUID
    game_id: UUID
    image_id: Optional[UUID]
    similarity_score: float
    image_url: Optional[str]
    page_number: Optional[int]
    
    # === CONTENU COMPLET DÉCOUPLÉ ===
    all_content: dict[str, Optional[str]]  # {"ocr": "...", "description": "...", "labels": "..."}
    
    def get_content_for_fields(self, fields: list[str]) -> str:
        """Retourne le contenu combiné pour les champs demandés"""
        contents = []
        for field in fields:
            if field in self.all_content and self.all_content[field]:
                contents.append(f"=== {field.upper()} ===\n{self.all_content[field]}")
        return "\n\n".join(contents)
    
    @property
    def content_snippet(self) -> str:
        """Retourne un extrait de tous les contenus disponibles pour affichage"""
        all_texts = []
        for field, content in self.all_content.items():
            if content:
                all_texts.append(f"{field}: {content[:100]}")
        combined = " | ".join(all_texts)
        if len(combined) > 200:
            return combined[:200] + "..."
        return combined
    
    def has_image(self) -> bool:
        """Vérifie si le résultat a une image associée"""
        return self.image_id is not None and self.image_url is not None
    
    def is_relevant(self, threshold: float) -> bool:
        """Vérifie si le résultat est pertinent selon un seuil"""
        return self.similarity_score >= threshold


@dataclass
class VectorSearchRequest:
    """Requête de recherche vectorielle"""
    
    game_id: UUID
    query: str
    top_k: int = 3
    similarity_threshold: float = 0.7
    include_images: bool = True
    
    def validate(self) -> None:
        """Valide les paramètres de la requête"""
        if self.top_k <= 0:
            raise ValueError("top_k doit être positif")
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold doit être entre 0.0 et 1.0")
        if not self.query.strip():
            raise ValueError("La requête ne peut pas être vide")


class IVectorSearchService(ABC):
    """Interface pour le service de recherche vectorielle"""
    
    @abstractmethod
    async def search_vectors(self, request: VectorSearchRequest) -> List[VectorSearchResult]:
        """
        Effectue une recherche vectorielle dans les documents d'un jeu spécifique
        
        Args:
            request: Paramètres de recherche
            
        Returns:
            Liste des résultats triés par score de similarité décroissant
        """
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding pour un texte donné
        
        Args:
            text: Texte à vectoriser
            
        Returns:
            Vecteur d'embedding
        """
        pass
    
    @abstractmethod
    async def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcule la similarité cosine entre deux embeddings
        
        Args:
            embedding1: Premier vecteur
            embedding2: Deuxième vecteur
            
        Returns:
            Score de similarité entre 0 et 1
        """
        pass