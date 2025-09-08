from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

@dataclass
class ProcessingJob:
  """Tâche de traitement d'image"""
  job_id: str
  image_id: UUID
  game_id: UUID
  blob_path: str
  filename: str
  batch_id: Optional[UUID] = None
  retry_count: int = 0
  max_retries: int = 3
  metadata: Optional[Dict[str, Any]] = None

class IQueueService(ABC):
  """Interface pour le service de queue"""

  @abstractmethod
  async def enqueue_image_processing(
      self, 
      image_id: UUID,
      game_id: UUID, 
      blob_path: str,
      filename: str,
      batch_id: Optional[UUID] = None
  ) -> str:
      """Ajoute une tâche de traitement d'image à la queue"""
      pass

  @abstractmethod
  async def get_job_status(self, job_id: str) -> Optional[str]:
      """Récupère le statut d'une tâche"""
      pass

  @abstractmethod
  async def mark_job_processing(self, job_id: str) -> None:
      """Marks a job as processing"""
      pass

  @abstractmethod
  async def mark_job_completed(self, job_id: str) -> None:
      """Marks a job as successful"""
      pass

  @abstractmethod
  async def mark_job_failed(self, job_id: str, error_message: str) -> None:
      """Marks a job as failed"""
      pass

  @abstractmethod
  async def retry_failed_job(self, job_id: str) -> bool:
      """Remet en queue une tâche échouée"""
      pass

  @abstractmethod
  async def dequeue_job(self) -> Optional[ProcessingJob]:
      """Gets the next task (with unconnection handling)"""
      pass

  @abstractmethod
  async def close(self) -> None:
      """Closes the Redis conection"""
      pass