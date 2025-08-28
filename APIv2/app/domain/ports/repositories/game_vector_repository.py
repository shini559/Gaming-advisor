from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.game_vector import GameVector


class IGameVectorRepository(ABC):
  """Interface pour le repository des vecteurs de jeu"""

  @abstractmethod
  async def create(self, vector: GameVector) -> GameVector:
      """Crée un nouveau vecteur"""
      pass

  @abstractmethod
  async def get_by_id(self, vector_id: UUID) -> Optional[GameVector]:
      """Récupère un vecteur par son ID"""
      pass

  @abstractmethod
  async def get_by_game_id(self, game_id: UUID) -> List[GameVector]:
      """Récupère tous les vecteurs d'un jeu"""
      pass

  @abstractmethod
  async def get_by_image_id(self, image_id: UUID) -> List[GameVector]:
      """Récupère tous les vecteurs d'une image"""
      pass

  @abstractmethod
  async def search_similar(
      self,
      game_id: UUID,
      query_vector: List[float],
      limit: int = 10
  ) -> List[GameVector]:
      """Recherche de vecteurs similaires pour un jeu donné"""
      pass

  @abstractmethod
  async def delete(self, vector_id: UUID) -> bool:
      """Supprime un vecteur"""
      pass

  @abstractmethod
  async def delete_by_image_id(self, image_id: UUID) -> int:
      """Supprime tous les vecteurs d'une image, retourne le nombre supprimé"""
      pass
