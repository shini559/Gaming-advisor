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

      # Store job data
      await redis_client.setex(
          f"{self.JOB_DATA_PREFIX}{job_id}",
          timedelta(hours=settings.redis_ttl),
          json.dumps(job_data)
      )

      # Add to queue
      await redis_client.lpush(self.QUEUE_NAME, job_id)

      # Mark as queued
      await self._set_job_status(job_id, "queued")

      return job_id

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
          redis_client = await self._get_redis()
          
          result = await redis_client.brpop(self.QUEUE_NAME, timeout=30)
          if not result:
              # Normal timeout - no error
              return None


          _, job_id = result # Get job_id

          job_data = await redis_client.get(f"{self.JOB_DATA_PREFIX}{job_id}")
          if not job_data:
              return None

          job_info = json.loads(job_data)

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
      except redis.TimeoutError:
          # Explicit timeout - normal behavior
          return None
      except (redis.ConnectionError, redis.RedisError, OSError) as e:
          # Connection error - force reconnection
          logger.warning(f"Redis: Erreur de connexion: {e}. Forçant la reconnexion...") if settings.debug else None
          self._redis = None
          return None
      except Exception as e:
          # Other error - log but no reconnection
          logger.error(f"Redis: Erreur inattendue lors du dequeue: {e}") if settings.debug else None
          return None

  async def close(self) -> None:
      """Closes the Redis conection"""
      if self._redis:
          await self._redis.aclose()