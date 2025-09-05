from typing import BinaryIO, Optional
from uuid import UUID

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.domain.ports.services.blob_storage_service import IBlobStorageService


class AzureBlobStorageService(IBlobStorageService):
  """Service pour gérer Azure Blob Storage"""

  def __init__(self):
      self._client = None

  @property
  def client(self) -> BlobServiceClient:
      """Lazy initialization du client Azure"""
      if self._client is None:
          if settings.azure_storage_connection_string:
              self._client = BlobServiceClient.from_connection_string(
                  settings.azure_storage_connection_string
              )
          else:
              raise ValueError("Azure Storage connection string not configured")
      return self._client

  async def upload_image(
      self,
      game_id: UUID,
      image_id: UUID,
      file_content: BinaryIO,
      filename: str,
      content_type: str
  ) -> tuple[str, str]:
      """Upload une image dans Azure Blob Storage"""

      # Structure: games/{game_id}/images/{image_id}_{filename}
      file_path = f"games/{game_id}/images/{image_id}_{filename}"

      # Obtenir le container client
      container_client = self.client.get_container_client(settings.azure_blob_container_name)

      # Upload du fichier
      blob_client = container_client.get_blob_client(file_path)

      # Lire le contenu du fichier
      file_content.seek(0)
      content = file_content.read()

      await blob_client.upload_blob(
          content,
          overwrite=True,
          content_type=content_type,
          metadata={
              "game_id": str(game_id),
              "image_id": str(image_id),
              "original_filename": filename
          }
      )

      # Construire l'URL publique
      blob_url = f"{settings.azure_blob_url}/{settings.azure_blob_container_name}/{file_path}"

      return file_path, blob_url

  async def download_image(self, file_path: str) -> bytes:
      """Télécharge le contenu d'une image depuis Azure Blob Storage"""
      try:
          container_client = self.client.get_container_client(
              settings.azure_blob_container_name
          )
          blob_client = container_client.get_blob_client(file_path)

          download_stream = await blob_client.download_blob()
          return await download_stream.readall()

      except Exception as e:
          raise ValueError(f"Failed to download image from {file_path}: {str(e)}")

  async def delete_image(self, file_path: str) -> bool:
      """Supprime une image d'Azure Blob Storage"""
      try:
          container_client = self.client.get_container_client(settings.azure_blob_container_name)
          blob_client = container_client.get_blob_client(file_path)
          await blob_client.delete_blob()
          return True
      except Exception:
          return False

  async def get_image_url(self, file_path: str, expires_in_hours: int = 24) -> Optional[str]:
      """Génère une URL signée temporaire pour accéder à l'image"""
      if not settings.azure_storage_key:
          # Si pas de clé, retourne l'URL publique (container public)
          return f"{settings.azure_blob_url}/{settings.azure_blob_container_name}/{file_path}"

      try:
          # Génère une URL signée avec expiration
          sas_token = generate_blob_sas(
              account_name=settings.azure_storage_account,
              container_name=settings.azure_blob_container_name,
              blob_name=file_path,
              account_key=settings.azure_storage_key,
              permission=BlobSasPermissions(read=True),
              expiry=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
          )

          return f"{settings.azure_blob_url}/{settings.azure_blob_container_name}/{file_path}?{sas_token}"
      except Exception:
          return None

  async def upload_game_avatar(
      self,
      game_id: UUID,
      file_content: bytes,
      filename: str,
      content_type: str
  ) -> tuple[str, str]:
      """Upload un avatar de jeu dans Azure Blob Storage"""
      
      # Structure: game_images/{game_id}/avatar_{filename}
      file_path = f"game_images/{game_id}/avatar_{filename}"
      
      # Obtenir le container client
      container_client = self.client.get_container_client(settings.azure_blob_container_name)
      
      # Upload du fichier
      blob_client = container_client.get_blob_client(file_path)
      
      try:
          # Upload avec métadonnées
          await blob_client.upload_blob(
              file_content,
              blob_type="BlockBlob",
              content_type=content_type,
              metadata={
                  "game_id": str(game_id),
                  "type": "avatar",
                  "original_filename": filename
              },
              overwrite=True  # Remplace l'avatar existant si il y en a un
          )
          
          # Générer l'URL publique
          blob_url = blob_client.url
          
          return file_path, blob_url
          
      except Exception as e:
          raise ValueError(f"Failed to upload avatar for game {game_id}: {str(e)}")

  async def close(self):
      """Ferme proprement la connexion Azure"""
      if self._client:
          await self._client.close()
          self._client = None
