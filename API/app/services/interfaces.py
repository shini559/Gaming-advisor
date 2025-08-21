from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional
from pathlib import Path


class VisionExtractor(Protocol):
    """Interface pour l'extraction de contenu d'images via IA"""
    
    async def extract_rules_from_image(self, image_path: Path) -> Dict[str, Any]:
        """Extrait les règles d'une image de livret"""
        ...


class EmbeddingService(Protocol):
    """Interface pour la génération d'embeddings"""
    
    async def embed_text(self, text: str) -> List[float]:
        """Génère un embedding pour un texte"""
        ...
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings pour une liste de textes"""
        ...


class VectorStore(Protocol):
    """Interface pour le stockage vectoriel"""
    
    async def create_collection(self, collection_name: str) -> bool:
        """Crée une nouvelle collection"""
        ...
    
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        embeddings: List[List[float]], 
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Ajoute des documents à la collection"""
        ...
    
    async def search(
        self, 
        collection_name: str, 
        query_embedding: List[float], 
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Recherche des documents similaires"""
        ...
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Supprime une collection"""
        ...


class FileStorage(Protocol):
    """Interface pour le stockage de fichiers"""
    
    async def save_file(self, file_path: Path, content: bytes) -> bool:
        """Sauvegarde un fichier"""
        ...
    
    async def load_file(self, file_path: Path) -> bytes:
        """Charge un fichier"""
        ...
    
    async def delete_file(self, file_path: Path) -> bool:
        """Supprime un fichier"""
        ...
    
    def get_game_folder(self, game_name: str) -> Path:
        """Retourne le chemin du dossier d'un jeu"""
        ...


class TextChunker(Protocol):
    """Interface pour le découpage de texte"""
    
    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Découpe un texte en chunks"""
        ...
    
    def chunk_json_content(self, json_data: Dict[str, Any], chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Découpe le contenu JSON extrait en chunks logiques"""
        ...


# Abstract base classes pour l'implémentation
class BaseVisionExtractor(ABC):
    """Classe de base pour l'extraction d'images"""
    
    @abstractmethod
    async def extract_rules_from_image(self, image_path: Path) -> Dict[str, Any]:
        pass


class BaseEmbeddingService(ABC):
    """Classe de base pour les embeddings"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass


class BaseVectorStore(ABC):
    """Classe de base pour le vector store"""
    
    @abstractmethod
    async def create_collection(self, collection_name: str) -> bool:
        pass
    
    @abstractmethod
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        embeddings: List[List[float]], 
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        pass
    
    @abstractmethod
    async def search(
        self, 
        collection_name: str, 
        query_embedding: List[float], 
        n_results: int = 5
    ) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        pass


class BaseFileStorage(ABC):
    """Classe de base pour le stockage de fichiers"""
    
    @abstractmethod
    async def save_file(self, file_path: Path, content: bytes) -> bool:
        pass
    
    @abstractmethod
    async def load_file(self, file_path: Path) -> bytes:
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: Path) -> bool:
        pass
    
    @abstractmethod
    def get_game_folder(self, game_name: str) -> Path:
        pass