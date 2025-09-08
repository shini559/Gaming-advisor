from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from uuid import UUID


class IBlobStorageService(ABC):
  """Interface pour le service de stockage Azure Blob"""

  @abstractmethod
  async def upload_image(
      self,
      game_id: UUID,
      image_id: UUID,
      file_content: BinaryIO,
      filename: str,
      content_type: str
  ) -> tuple[str, str]:
      """
      Upload une image dans Azure Blob Storage

      Returns:
          tuple[file_path, blob_url] - Le path interne et l'URL publique
      """
      pass

  @abstractmethod
  async def download_image(self, file_path: str) -> bytes:
      """Télécharge le contenu d'une image depuis le stockage"""
      pass

  @abstractmethod
  async def delete_image(self, file_path: str) -> bool:
      """Supprime une image d'Azure Blob Storage"""
      pass

  @abstractmethod
  async def get_image_url(self, file_path: str, expires_in_hours: int = 24) -> Optional[str]:
      """Génère une URL signée temporaire pour accéder à l'image"""
      pass

  @abstractmethod
  async def upload_game_avatar(
      self,
      game_id: UUID,
      file_content: bytes,
      filename: str,
      content_type: str
  ) -> tuple[str, str]:
      """
      Upload un avatar de jeu dans Azure Blob Storage
      
      Args:
          game_id: ID du jeu
          file_content: Contenu du fichier avatar
          filename: Nom du fichier original
          content_type: Type MIME du fichier
      
      Returns:
          tuple[file_path, blob_url] - Le path interne et l'URL publique
      """
      pass

  @abstractmethod
  async def close(self):
      """Ferme proprement la connexion Azure"""
      pass