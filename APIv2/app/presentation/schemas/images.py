from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List


class ImageUploadResponse(BaseModel):
  """Schema de réponse pour l'upload d'image"""
  image_id: UUID = Field(..., description="ID unique de l'image")
  job_id: str = Field(..., description="ID de la tâche de traitement")
  status: str = Field(..., description="Statut de l'upload (uploaded, error)")
  message: str = Field(..., description="Message descriptif")
  blob_url: str = Field(..., description="URL de l'image dans Azure Blob Storage")

  model_config = {
      "json_schema_extra": {
          "example": {
              "image_id": "550e8400-e29b-41d4-a716-446655440000",
              "job_id": "optional",
              "status": "uploaded",
              "message": "Image uploaded successfully, processing queued",
              "blob_url": "https://gameadvisor.blob.core.windows.net/images/..."
          }
      }
  }


class ImageStatusResponse(BaseModel):
  """Schema de réponse pour le statut de traitement"""
  image_id: UUID = Field(..., description="ID unique de l'image")
  job_id: Optional[str] = Field(None, description="ID de la tâche de traitement")
  status: str = Field(..., description="Statut du traitement")
  progress: Optional[str] = Field(None, description="Détail du progrès")
  error_message: Optional[str] = Field(None, description="Message d'erreur si échec")
  created_at: str = Field(..., description="Date de création")
  processing_started_at: Optional[str] = Field(None, description="Date de début du traitement")
  processing_completed_at: Optional[str] = Field(None, description="Date de fin du traitement")
  retry_count: int = Field(..., description="Nombre de tentatives")


class BatchUploadResponse(BaseModel):
  """Schema de réponse pour l'upload de batch d'images"""
  batch_id: UUID = Field(..., description="ID unique du batch")
  total_images: int = Field(..., description="Nombre total d'images dans le batch")
  uploaded_images: int = Field(..., description="Nombre d'images uploadées avec succès")
  status: str = Field(..., description="Statut du batch")
  message: str = Field(..., description="Message descriptif")
  job_ids: List[str] = Field(..., description="IDs des tâches de traitement")

  model_config = {
      "json_schema_extra": {
          "example": {
              "batch_id": "550e8400-e29b-41d4-a716-446655440000",
              "total_images": 25,
              "uploaded_images": 25,
              "status": "pending",
              "message": "Batch créé avec succès, traitement en attente",
              "job_ids": ["job_123", "job_124", "job_125"]
          }
      }
  }


class BatchStatusResponse(BaseModel):
  """Schema de réponse pour le statut de batch"""
  batch_id: UUID = Field(..., description="ID unique du batch")
  status: str = Field(..., description="Statut du batch")
  total_images: int = Field(..., description="Nombre total d'images")
  processed_images: int = Field(..., description="Images traitées avec succès")
  failed_images: int = Field(..., description="Images en échec")
  progress_ratio: str = Field(..., description="Ratio de progression (ex: '5/30')")
  failed_ratio: str = Field(..., description="Ratio d'échecs (ex: '2/30')")
  completion_percentage: float = Field(..., description="Pourcentage de completion")
  failure_percentage: float = Field(..., description="Pourcentage d'échecs")
  can_retry: bool = Field(..., description="Peut être retrié")
  retry_count: int = Field(..., description="Nombre de tentatives actuelles")
  max_retries: int = Field(..., description="Nombre maximum de tentatives")
  progress_message: str = Field(..., description="Message détaillé de progression")
  created_at: str = Field(..., description="Date de création")
  processing_started_at: Optional[str] = Field(None, description="Date de début du traitement")
  completed_at: Optional[str] = Field(None, description="Date de fin du traitement")

  model_config = {
      "json_schema_extra": {
          "example": {
              "batch_id": "550e8400-e29b-41d4-a716-446655440000",
              "status": "processing",
              "total_images": 30,
              "processed_images": 5,
              "failed_images": 2,
              "progress_ratio": "5/30",
              "failed_ratio": "2/30",
              "completion_percentage": 16.67,
              "failure_percentage": 6.67,
              "can_retry": True,
              "retry_count": 0,
              "max_retries": 3,
              "progress_message": "En cours - 5/30 images traitées",
              "created_at": "2025-08-27T16:30:00Z",
              "processing_started_at": "2025-08-27T16:30:15Z",
              "completed_at": None
          }
      }
  }
