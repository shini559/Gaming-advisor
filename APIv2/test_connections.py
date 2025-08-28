"""
Script simple pour tester les connexions Azure et Redis
Usage: python test_connections.py
"""

import asyncio
import sys
from io import BytesIO
from uuid import uuid4

from app.config import settings
from app.services.blob_storage_service import AzureBlobStorageService
from app.services.redis_queue_service import RedisQueueService
from app.domain.ports.services.queue_service import ProcessingJob


async def test_azure_blob() -> bool|None:
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

        return True

    except Exception as e:
        print(f"   ❌ Azure Blob Storage Error: {e}")
        return False

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


async def test_redis_queue() -> bool|None:
  """Test de connexion Redis"""
  print("🔴 Testing Redis Queue...")

  service = None
  job_id = None

  try:
      service = RedisQueueService()

      # Créer un job de test
      test_job = ProcessingJob(
          job_id=f"test_job_{uuid4().hex[:8]}",
          image_id=uuid4(),
          game_id=uuid4(),
          blob_path="test/path.jpg",
          filename="test.jpg",
          metadata={"test": True}
      )

      print(f"   Enqueueing test job: {test_job.job_id}")
      job_id = await service.enqueue_image_processing(test_job)
      print(f"   ✅ Job enqueued: {job_id}")

      # Vérifier le statut
      status = await service.get_job_status(job_id)
      print(f"   📊 Job status: {status}")

      return True

  except Exception as e:
      print(f"   ❌ Redis Queue Error: {e}")
      return False

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


def test_config() -> bool:
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
      print(f"   🤖 Vision Model: {settings.azure_openai_vision_model}")
      print(f"   🧮 Embedding Model: {settings.azure_openai_embedding_model}")
  else:
      print(f"   ⚠️  OpenAI: Not configured (optional for connection test)")

  # Image settings
  print(f"   📐 Image Max Size: {settings.image_max_file_size_mb}MB")
  print(f"   📏 Image Max Dims: {settings.image_max_width}x{settings.image_max_height}")

  return config_ok


async def main() -> bool:
  """Test principal"""
  print("🚀 GameAdvisor API v2 - Connection Tests")
  print("=" * 50)

  # Test config
  config_ok = test_config()
  print()

  if not config_ok:
      print("❌ Configuration incomplete. Check your .env file.")
      return False

  results = []

  # Test Azure Blob
  azure_ok = await test_azure_blob()
  results.append(("Azure Blob Storage", azure_ok))
  print()

  # Test Redis
  redis_ok = await test_redis_queue()
  results.append(("Redis Queue", redis_ok))
  print()

  # Résultats
  print("📊 Test Results:")
  print("-" * 30)

  all_ok = True
  for service, ok in results:
      status = "✅ PASS" if ok else "❌ FAIL"
      print(f"   {service:<20} {status}")
      if not ok:
          all_ok = False

  print()
  if all_ok:
      print("🎉 All connections successful! Your setup is ready.")
  else:
      print("⚠️  Some connections failed. Check configuration and services.")

  return all_ok


if __name__ == "__main__":
  try:
      success = asyncio.run(main())
      sys.exit(0 if success else 1)
  except KeyboardInterrupt:
      print("\n⏹️  Test interrupted by user")
      sys.exit(1)
  except Exception as e:
      print(f"\n💥 Unexpected error: {e}")
      sys.exit(1)


