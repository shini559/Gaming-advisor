"""
Tests de connexion aux dépendances externes (Azure, Redis)
Usage: pytest -m connection -v
"""

import asyncio
import sys
import pytest
from io import BytesIO
from uuid import uuid4

from app.config import settings
from app.services.blob_storage_service import AzureBlobStorageService
from app.services.redis_queue_service import RedisQueueService


@pytest.mark.connection
@pytest.mark.external_deps
@pytest.mark.asyncio
async def test_azure_blob_connection():
    """Test de connexion Azure Blob Storage"""
    print("🔵 Testing Azure Blob Storage...")

    service = None
    file_path = None

    try:
        service = AzureBlobStorageService()

        # Test avec un petit fichier
        test_content = b"Test image content for GameAdvisor"
        filename = f"test_image_{uuid4().hex[:8]}.jpg"

        # Path direct dans test/ au lieu de games/
        file_path = f"test/{filename}"

        print(f"   Uploading test file: {filename}")

        # Upload direct sans passer par upload_image()
        container_client = service.client.get_container_client(settings.azure_blob_container_name)
        blob_client = container_client.get_blob_client(file_path)

        await blob_client.upload_blob(
            test_content,
            overwrite=True,
            content_type="image/jpeg"
        )

        blob_url = f"{settings.azure_blob_url}/{settings.azure_blob_container_name}/{file_path}"

        print(f"   ✅ Upload successful!")
        print(f"   📁 File path: {file_path}")
        print(f"   🔗 Blob URL: {blob_url}")

        assert True, "Azure Blob Storage connection successful"

    except Exception as e:
        error_msg = str(e)
        if "Request date header too old" in error_msg:
            pytest.fail(f"Azure Blob Storage Error: Horloge système désynchronisée. Vérifiez l'heure système ou la configuration des certificats SSL. Détail: {e}")
        elif "AuthenticationFailed" in error_msg:
            pytest.fail(f"Azure Blob Storage Error: Authentification échouée. Vérifiez AZURE_STORAGE_CONNECTION_STRING et AZURE_STORAGE_KEY dans .env. Détail: {e}")
        else:
            pytest.fail(f"Azure Blob Storage Error: {e}")

    finally:
        # Nettoyage du fichier
        if file_path and service:
            try:
                print(f"   🗑️  Cleaning up test file...")
                deleted = await service.delete_image(file_path)
                print(f"   ✅ Cleanup: {'Success' if deleted else 'Failed'}")
            except Exception as cleanup_error:
                print(f"   ⚠️ Cleanup failed: {cleanup_error}")
        
        # Fermeture du service
        if service and hasattr(service, 'close'):
            try:
                await service.close()
            except Exception as close_error:
                print(f"   ⚠️ Service close failed: {close_error}")


@pytest.mark.connection
@pytest.mark.external_deps
@pytest.mark.asyncio
async def test_redis_queue_connection():
  """Test de connexion Redis"""
  print("🔴 Testing Redis Queue...")

  service = None
  job_id = None

  try:
      service = RedisQueueService()

      # Paramètres de test
      test_image_id = uuid4()
      test_game_id = uuid4()
      test_blob_path = "test/path.jpg"
      test_filename = "test.jpg"
      
      print(f"   Enqueueing test job for image: {test_image_id}")
      job_id = await service.enqueue_image_processing(
          image_id=test_image_id,
          game_id=test_game_id,
          blob_path=test_blob_path,
          filename=test_filename
      )
      print(f"   ✅ Job enqueued: {job_id}")

      # Vérifier le statut
      status = await service.get_job_status(job_id)
      print(f"   📊 Job status: {status}")

      assert True, "Redis Queue connection successful"

  except Exception as e:
      pytest.fail(f"Redis Queue Error: {e}")

  finally:
      # Nettoyage garanti
      if service:
          try:
              # Nettoyer le job de test si possible
              if job_id:
                  # TODO: Ajouter méthode pour supprimer un job de test
                  pass

              await service.close()
              print(f"   ✅ Connection closed")
          except Exception as close_error:
              print(f"   ⚠️ Service close failed: {close_error}")


@pytest.mark.connection
def test_config():
  """Test de configuration"""
  print("⚙️  Testing Configuration...")

  config_ok = True

  # Azure Storage
  if settings.azure_storage_connection_string:
      print(f"   ✅ Azure Storage: Configured")
      print(f"   📦 Container: {settings.azure_blob_container_name}")
      if settings.azure_storage_account:
          print(f"   🏪 Account: {settings.azure_storage_account}")
  else:
      print(f"   ❌ Azure Storage: Not configured")
      config_ok = False

  # Redis
  if settings.redis_url:
      print(f"   ✅ Redis: Configured ({settings.redis_url})")
  else:
      print(f"   ❌ Redis: Not configured")
      config_ok = False

  # OpenAI
  if settings.azure_openai_api_key:
      print(f"   ✅ OpenAI: Configured")
      print(f"   🤖 Vision Deployment: {settings.azure_openai_vision_deployment}")
      print(f"   🧮 Embedding Deployment: {settings.azure_openai_embedding_deployment}")
  else:
      print(f"   ⚠️  OpenAI: Not configured (optional for connection test)")

  # Image settings
  print(f"   📐 Image Max Size: {settings.image_max_file_size_mb}MB")
  print(f"   📏 Image Max Dims: {settings.image_max_width}x{settings.image_max_height}")

  assert config_ok, "Configuration incomplete. Check your .env file."


# Pour exécuter ces tests :
# pytest -m connection -v  # Tests de connexion uniquement
# pytest -m external_deps -v  # Tous les tests de dépendances externes


