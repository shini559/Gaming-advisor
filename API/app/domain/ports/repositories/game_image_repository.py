from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.game_image import GameImage, ImageProcessingStatus


class IGameImageRepository(ABC):
  """Interface pour le repository des images de jeu"""

  @abstractmethod
  async def create(self, image: GameImage) -> GameImage:
      """Crée une nouvelle image"""
      pass

  @abstractmethod
  async def get_by_id(self, image_id: UUID) -> Optional[GameImage]:
      """Récupère une image par son ID"""
      pass

  @abstractmethod
  async def get_by_game_id(self, game_id: UUID) -> List[GameImage]:
      """Récupère toutes les images d'un jeu"""
      pass

  @abstractmethod
  async def get_by_status(self, status: ImageProcessingStatus) -> List[GameImage]:
      """Récupère les images par statut de traitement"""
      pass

  @abstractmethod
  async def update(self, image: GameImage) -> GameImage:
      """Met à jour une image"""
      pass

  @abstractmethod
  async def delete(self, image_id: UUID) -> bool:
      """Supprime une image"""
      pass