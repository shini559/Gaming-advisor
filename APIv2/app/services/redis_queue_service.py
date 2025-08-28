import json
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

import redis.asyncio as redis

from app.config import settings
from app.domain.ports.services.queue_service import IQueueService, ProcessingJob


class RedisQueueService(IQueueService):
  """Service de queue basé sur Redis"""

  QUEUE_NAME = "image_processing_queue"
  STATUS_PREFIX = "job_status:"
  JOB_DATA_PREFIX = "job_data:"

  def __init__(self):
      self._redis: Optional[redis.Redis] = None

  async def _get_redis(self) -> redis.Redis:
      """Lazy initialization de la connexion Redis"""
      if self._redis is None:
          if hasattr(settings, 'redis_host') and settings.redis_host:
              # Configuration avec paramètres séparés (Azure)
              self._redis = redis.Redis(
                  host=settings.redis_host,
                  port=settings.redis_port,
                  password=settings.redis_password,
                  ssl=settings.redis_ssl,
                  ssl_cert_reqs=ssl.CERT_NONE if settings.redis_ssl else None,
                  ssl_check_hostname=False if settings.redis_ssl else None,
                  decode_responses=True  # ← Garde cette option
              )
          else:
              # URL Redis
              self._redis = redis.from_url(
                  settings.redis_url,
                  decode_responses=True
              )
      return self._redis

  async def enqueue_image_processing(
      self,
      image_id: UUID,
      game_id: UUID, 
      blob_path: str,
      filename: str,
      batch_id: Optional[UUID] = None
  ) -> str:
      """Ajoute une tâche de traitement d'image à la queue"""
      redis_client = await self._get_redis()

      # Générer un job_id unique
      job_id = f"job_{image_id}_{datetime.utcnow().timestamp()}"

      # Sérialiser la tâche
      job_data = {
          "job_id": job_id,
          "image_id": str(image_id),
          "game_id": str(game_id),
          "blob_path": blob_path,
          "filename": filename,
          "batch_id": str(batch_id) if batch_id else None,
          "retry_count": 0,
          "max_retries": settings.queue_retry_attempts,
          "metadata": {},
          "created_at": datetime.utcnow().isoformat(),
      }

      # Stocker les données de la tâche
      await redis_client.setex(
          f"{self.JOB_DATA_PREFIX}{job_id}",
          timedelta(hours=24),  # TTL de 24h
          json.dumps(job_data)
      )

      # Ajouter à la queue
      await redis_client.lpush(self.QUEUE_NAME, job_id)

      # Marquer comme en attente
      await self._set_job_status(job_id, "queued")

      return job_id

  async def get_job_status(self, job_id: str) -> Optional[str]:
      """Récupère le statut d'une tâche"""
      redis_client = await self._get_redis()
      status = await redis_client.get(f"{self.STATUS_PREFIX}{job_id}")
      return status if status else None

  async def retry_failed_job(self, job_id: str) -> bool:
      """Remet en queue une tâche échouée"""
      redis_client = await self._get_redis()

      # Récupérer les données de la tâche
      job_data = await redis_client.get(f"{self.JOB_DATA_PREFIX}{job_id}")
      if not job_data:
          return False

      job_info = json.loads(job_data)

      # Vérifier si on peut encore réessayer
      if job_info["retry_count"] >= job_info["max_retries"]:
          return False

      # Incrémenter le compteur de retry
      job_info["retry_count"] += 1
      job_info["retried_at"] = datetime.utcnow().isoformat()

      # Mettre à jour les données
      await redis_client.setex(
          f"{self.JOB_DATA_PREFIX}{job_id}",
          timedelta(hours=24),
          json.dumps(job_info)
      )

      # Remettre en queue
      await redis_client.lpush(self.QUEUE_NAME, job_id)
      await self._set_job_status(job_id, "retrying")

      return True

  async def _set_job_status(self, job_id: str, status: str) -> None:
      """Met à jour le statut d'une tâche"""
      redis_client = await self._get_redis()
      await redis_client.setex(
          f"{self.STATUS_PREFIX}{job_id}",
          timedelta(hours=24),
          status
      )

  async def dequeue_job(self) -> Optional[ProcessingJob]:
      """Récupère la prochaine tâche à traiter"""
      redis_client = await self._get_redis()

      result = await redis_client.brpop(self.QUEUE_NAME, timeout=30)
      if not result:
          return None

      _, job_id = result
      # job_id est déjà une string, pas besoin de decode

      job_data = await redis_client.get(f"{self.JOB_DATA_PREFIX}{job_id}")
      if not job_data:
          return None

      job_info = json.loads(job_data)  # job_data est déjà une string

      return ProcessingJob(
          job_id=job_info["job_id"],
          image_id=UUID(job_info["image_id"]),
          game_id=UUID(job_info["game_id"]),
          blob_path=job_info["blob_path"],
          filename=job_info["filename"],
          retry_count=job_info["retry_count"],
          max_retries=job_info["max_retries"],
          metadata=job_info["metadata"]
      )

  async def mark_job_processing(self, job_id: str) -> None:
      """Marque une tâche comme en cours de traitement"""
      await self._set_job_status(job_id, "processing")

  async def mark_job_completed(self, job_id: str) -> None:
      """Marque une tâche comme terminée avec succès"""
      await self._set_job_status(job_id, "completed")

  async def mark_job_failed(self, job_id: str, error_message: str) -> None:
      """Marque une tâche comme échouée"""
      redis_client = await self._get_redis()
      await self._set_job_status(job_id, "failed")

      # Stocker le message d'erreur
      await redis_client.setex(
          f"job_error:{job_id}",
          timedelta(hours=24),
          error_message
      )

  async def close(self) -> None:
      """Ferme la connexion Redis"""
      if self._redis:
          await self._redis.aclose()