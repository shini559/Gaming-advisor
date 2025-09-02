import json
import ssl
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import redis.asyncio as redis

from app.config import settings
from app.domain.ports.services.queue_service import IQueueService, ProcessingJob

logger = logging.getLogger(__name__)


class RedisQueueService(IQueueService):
  """Queue service using Redis"""

  QUEUE_NAME = "image_processing_queue"
  STATUS_PREFIX = "job_status:"
  JOB_DATA_PREFIX = "job_data:"

  def __init__(self):
      self._redis: Optional[redis.Redis] = None

  async def _get_redis(self) -> redis.Redis:
      """Lazy initialization for Redis with automatic reconnection"""

      if self._redis is None:
          logger.info("Redis: First connection...") if settings.debug else None
          await self._create_connection()
      elif not await self._test_connection():
          logger.warning("Redis: connection lost, reconnecting...") if settings.debug else None
          await self._create_connection()
          logger.info("Redis: Reconnected") if settings.debug else None
      return self._redis
  
  async def _create_connection(self) -> None:
      """Creates a new Redis connection"""

      if self._redis:
          logger.debug("Redis: Closing previous connection") if settings.debug else None
          try:
              await self._redis.aclose()
          except Exception as e:
              logger.debug(f"Redis: Error while closing connection: {e}") if settings.debug else None
      
      logger.info(f"Redis: Connecting to {settings.redis_host}:{settings.redis_port}") if settings.debug else None
      
      if hasattr(settings, 'redis_host') and settings.redis_host:
          # Redis configuration (separate for production and testing)
          redis_config = {
              "host": settings.redis_host,
              "port": settings.redis_port,
              "password": settings.redis_password,
              "decode_responses": True,
              "socket_timeout": 10.0,
              "socket_connect_timeout": 10.0,
              "retry_on_timeout": True,
              "health_check_interval": 30
          }
          if settings.redis_ssl:
              redis_config.update({
                  "ssl": True,
                  "ssl_cert_reqs": ssl.CERT_NONE,
                  "ssl_check_hostname": False
              })
          self._redis = redis.Redis(**redis_config)

      else:
          # For testing and local development
          self._redis = redis.from_url(
              settings.redis_url,
              decode_responses=True,
              socket_timeout=10.0,
              socket_connect_timeout=10.0,
              retry_on_timeout=True,
              health_check_interval=30
          )
      
      # New connection test
      try:
          await self._redis.ping()
          logger.info("Redis: Connection established") if settings.debug else None
      except Exception as e:
          logger.error(f"Redis: Connection failure: {e}") if settings.debug else None
          raise
  
  async def _test_connection(self) -> bool:
      """Tests if Redis connection is active"""

      if self._redis is None:
          return False
      try:
          await self._redis.ping()
          return True
      except Exception as e:
          logger.debug(f"Redis: Connection test failed: {e}") if settings.debug else None
          return False

  async def enqueue_image_processing(
      self,
      image_id: UUID,
      game_id: UUID, 
      blob_path: str,
      filename: str,
      batch_id: Optional[UUID] = None
  ) -> str:
      """Adds an image treatment job to the queue"""

      if settings.debug:
          logging.info(f"[REDIS_DEBUG] Enqueue - Image: {image_id}, Batch: {batch_id}, Filename: {filename}")

      try:
          redis_client = await self._get_redis()

          # Generate a unique job ID
          job_id = f"job_{image_id}_{datetime.now(timezone.utc).timestamp()}"

          # Serialize job
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
              "created_at": datetime.now(timezone.utc).isoformat(),
          }

          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Job data created - Job ID: {job_id}")

          # Store job data
          await redis_client.setex(
              f"{self.JOB_DATA_PREFIX}{job_id}",
              timedelta(hours=settings.redis_ttl),
              json.dumps(job_data)
          )

          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Job data stored in Redis")

          # Add to queue
          await redis_client.lpush(self.QUEUE_NAME, job_id)

          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Job added to queue: {self.QUEUE_NAME}")

          # Mark as queued
          await self._set_job_status(job_id, "queued")

          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Job {job_id} successfully enqueued")

          return job_id

      except Exception as e:
          if settings.debug:
              logging.error(f"[REDIS_DEBUG] ERREUR lors de l'enqueue:")
              logging.error(f"[REDIS_DEBUG] - Image ID: {image_id}")
              logging.error(f"[REDIS_DEBUG] - Batch ID: {batch_id}")
              logging.error(f"[REDIS_DEBUG] - Filename: {filename}")
              logging.error(f"[REDIS_DEBUG] - Erreur: {str(e)}")
              logging.error(f"[REDIS_DEBUG] - Type: {type(e).__name__}")
          raise

  async def get_job_status(self, job_id: str) -> Optional[str]:
      """Gets the status for a job"""

      redis_client = await self._get_redis()
      status = await redis_client.get(f"{self.STATUS_PREFIX}{job_id}")
      return status if status else None

  async def retry_failed_job(self, job_id: str) -> bool:
      """Puts back a failed job in queue"""

      redis_client = await self._get_redis()

      # Get job data
      job_data = await redis_client.get(f"{self.JOB_DATA_PREFIX}{job_id}")
      if not job_data:
          return False

      job_info = json.loads(job_data)

      # Check if it can be tried again
      if job_info["retry_count"] >= job_info["max_retries"]:
          return False

      # Increment retry counter
      job_info["retry_count"] += 1
      job_info["retried_at"] = datetime.now(timezone.utc).isoformat()

      # Update data
      await redis_client.setex(
          f"{self.JOB_DATA_PREFIX}{job_id}",
          timedelta(hours=settings.redis_ttl),
          json.dumps(job_info)
      )

      # Put back in queue
      await redis_client.lpush(self.QUEUE_NAME, job_id)
      await self._set_job_status(job_id, "retrying")

      return True

  async def _set_job_status(self, job_id: str, status: str) -> None:
      """Updates a job status"""

      redis_client = await self._get_redis()
      await redis_client.setex(
          f"{self.STATUS_PREFIX}{job_id}",
          timedelta(hours=settings.redis_ttl),
          status
      )

  async def mark_job_processing(self, job_id: str) -> None:
      """Marks a job as processing"""
      await self._set_job_status(job_id, "processing")

  async def mark_job_completed(self, job_id: str) -> None:
      """Marks a job as successful"""
      await self._set_job_status(job_id, "completed")

  async def mark_job_failed(self, job_id: str, error_message: str) -> None:
      """Marks a job as failed"""
      redis_client = await self._get_redis()
      await self._set_job_status(job_id, "failed")
      # Stocker le message d'erreur
      await redis_client.setex(
          f"job_error:{job_id}",
          timedelta(hours=24),
          error_message
      )

  async def dequeue_job(self) -> Optional[ProcessingJob]:
      """Gets the next task (with unconnection handling)"""

      try:
          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Attempting to dequeue from {self.QUEUE_NAME} (timeout: 30s)")
          
          redis_client = await self._get_redis()
          
          result = await redis_client.brpop(self.QUEUE_NAME, timeout=30)
          if not result:
              # Normal timeout - no error
              if settings.debug:
                  logging.info(f"[REDIS_DEBUG] Dequeue timeout (normal - no jobs available)")
              return None

          _, job_id = result # Get job_id

          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Dequeued job ID: {job_id}")

          job_data = await redis_client.get(f"{self.JOB_DATA_PREFIX}{job_id}")
          if not job_data:
              if settings.debug:
                  logging.error(f"[REDIS_DEBUG] PROBLÈME: Job data not found for {job_id}")
                  logging.error(f"[REDIS_DEBUG] Key recherchée: {self.JOB_DATA_PREFIX}{job_id}")
              return None

          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Job data retrieved successfully for {job_id}")

          try:
              job_info = json.loads(job_data)
          except json.JSONDecodeError as e:
              if settings.debug:
                  logging.error(f"[REDIS_DEBUG] ERREUR JSON decode pour {job_id}: {str(e)}")
                  logging.error(f"[REDIS_DEBUG] Raw job data: {job_data}")
              return None

          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Creating ProcessingJob object:")
              logging.info(f"[REDIS_DEBUG] - Job ID: {job_info['job_id']}")
              logging.info(f"[REDIS_DEBUG] - Image ID: {job_info['image_id']}")
              logging.info(f"[REDIS_DEBUG] - Game ID: {job_info['game_id']}")
              logging.info(f"[REDIS_DEBUG] - Batch ID: {job_info.get('batch_id', 'None')}")
              logging.info(f"[REDIS_DEBUG] - Filename: {job_info['filename']}")
              logging.info(f"[REDIS_DEBUG] - Retry: {job_info['retry_count']}/{job_info['max_retries']}")

          return ProcessingJob(
              job_id=job_info["job_id"],
              image_id=UUID(job_info["image_id"]),
              game_id=UUID(job_info["game_id"]),
              blob_path=job_info["blob_path"],
              filename=job_info["filename"],
              batch_id=UUID(job_info["batch_id"]) if job_info.get("batch_id") else None,
              retry_count=job_info["retry_count"],
              max_retries=job_info["max_retries"],
              metadata=job_info["metadata"]
          )
      except redis.TimeoutError:
          # Explicit timeout - normal behavior
          if settings.debug:
              logging.info(f"[REDIS_DEBUG] Redis timeout (normal)")
          return None
      except (redis.ConnectionError, redis.RedisError, OSError) as e:
          # Connection error - force reconnection
          if settings.debug:
              logging.error(f"[REDIS_DEBUG] Erreur de connexion: {e}. Forçant la reconnexion...")
          self._redis = None
          return None
      except Exception as e:
          # Other error - log but no reconnection
          if settings.debug:
              logging.error(f"[REDIS_DEBUG] Erreur inattendue lors du dequeue:")
              logging.error(f"[REDIS_DEBUG] - Erreur: {str(e)}")
              logging.error(f"[REDIS_DEBUG] - Type: {type(e).__name__}")
              import traceback
              logging.error(f"[REDIS_DEBUG] Stack trace: {traceback.format_exc()}")
          return None

  async def close(self) -> None:
      """Closes the Redis conection"""
      if self._redis:
          await self._redis.aclose()