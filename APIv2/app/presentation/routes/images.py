from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from starlette import status
from uuid import UUID
from typing import List

from app.dependencies import get_upload_image_use_case, get_current_user, get_get_image_status_use_case
from app.dependencies.batches import get_create_image_batch_use_case, get_get_batch_status_use_case
from app.domain.use_cases.images import UploadImageUseCase, UploadImageRequest
from app.domain.use_cases.images.get_image_status import GetImageStatusUseCase, GetImageStatusRequest
from app.domain.use_cases.images.create_image_batch import CreateImageBatchUseCase, CreateImageBatchRequest
from app.domain.use_cases.images.get_batch_status import GetBatchStatusUseCase
from app.presentation.schemas.images import ImageUploadResponse, ImageStatusResponse, BatchUploadResponse, BatchStatusResponse
from app.presentation.schemas.auth import ErrorResponse
from app.domain.entities.user import User


router = APIRouter(prefix="/images", tags=["Images"])


@router.post(
  "/games/{game_id}/upload",
  response_model=ImageUploadResponse,
  status_code=status.HTTP_202_ACCEPTED,
  responses={
      202: {"description": "Image uploaded, processing queued"},
      400: {"model": ErrorResponse, "description": "Invalid file or parameters"},
      404: {"model": ErrorResponse, "description": "Game not found"},
      413: {"model": ErrorResponse, "description": "File too large"},
      415: {"model": ErrorResponse, "description": "Unsupported media type"},
      500: {"model": ErrorResponse, "description": "Internal server error"}
  },
  summary="Upload game rulebook image",
  description="""
  Upload an image of game rulebook for AI processing and vectorization.

  The image will be:
  1. Uploaded to Azure Blob Storage
  2. Queued for AI processing (OCR + visual analysis)
  3. Vectorized and stored for RAG retrieval

  Returns immediately with 202 Accepted and job ID for tracking.
  """
)
async def upload_game_image(
  game_id: UUID,
  file: UploadFile = File(..., description="Image file (JPG/PNG, max 1MB, max 1000x1000)"),
  current_user: User = Depends(get_current_user),
  use_case: UploadImageUseCase = Depends(get_upload_image_use_case)
) -> ImageUploadResponse:
  """Upload une image de règles de jeu pour traitement IA"""

  # Validation des en-têtes
  if not file.content_type or not file.content_type.startswith('image/'):
      raise HTTPException(
          status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
          detail="File must be an image (JPEG/PNG)"
      )

  # Lire le contenu du fichier
  try:
      content = await file.read()
      file_size = len(content)

      # Créer un BytesIO pour le traitement
      from io import BytesIO
      file_stream = BytesIO(content)

      # Créer la requête
      request = UploadImageRequest(
          game_id=game_id,
          file_content=file_stream,
          filename=file.filename or "unknown.jpg",
          content_type=file.content_type,
          file_size=file_size,
          uploaded_by=current_user.id
      )

      # Exécuter l'upload
      response = await use_case.execute(request)

      if not response.success:
          if "not found" in response.message.lower():
              raise HTTPException(
                  status_code=status.HTTP_404_NOT_FOUND,
                  detail=response.message
              )
          elif "file" in response.message.lower():
              raise HTTPException(
                  status_code=status.HTTP_400_BAD_REQUEST,
                  detail=response.message
              )
          else:
              raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail=response.message
              )

      return ImageUploadResponse(
          image_id=response.image_id,
          job_id=response.job_id,
          status=response.status,
          message=response.message,
          blob_url=response.blob_url
      )

  except HTTPException:
      raise
  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=f"Upload failed: {str(e)}"
      )


@router.get(
    "/{image_id}/status",
    response_model=ImageStatusResponse,
    responses={
        200: {"description": "Image processing status"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Image not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get image processing status",
    description="Get the current status of image processing (uploaded, processing, completed, failed)"
)
async def get_image_processing_status(
        image_id: UUID,
        current_user: User = Depends(get_current_user),
        use_case: GetImageStatusUseCase = Depends(get_get_image_status_use_case)
) -> ImageStatusResponse:
    """Récupère le statut de traitement d'une image"""

    request = GetImageStatusRequest(
        image_id=image_id,
        user_id=current_user.id
    )

    response = await use_case.execute(request)

    if not response.success:
        if "not found" in response.error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.error_message
            )
        elif "access denied" in response.error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=response.error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error_message
            )

    return response


@router.post(
    "/games/{game_id}/batch-upload",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Batch uploaded, processing queued"},
        400: {"model": ErrorResponse, "description": "Invalid files or parameters"},
        404: {"model": ErrorResponse, "description": "Game not found"},
        413: {"model": ErrorResponse, "description": "Files too large"},
        415: {"model": ErrorResponse, "description": "Unsupported media type"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Upload multiple game rulebook images",
    description="Upload multiple images for a game as a batch. All images will be processed in parallel."
)
async def upload_game_images_batch(
        game_id: UUID,
        files: List[UploadFile] = File(..., description="Image files to upload"),
        current_user: User = Depends(get_current_user),
        use_case: CreateImageBatchUseCase = Depends(get_create_image_batch_use_case)
) -> BatchUploadResponse:
    """Upload multiple images as a batch"""
    
    try:
        # Validation des fichiers
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Au moins une image est requise"
            )

        # Préparer les fichiers pour le use case
        image_files = []
        for file in files:
            content = await file.read()
            image_files.append((file.filename or "unknown", content, len(content)))

        request = CreateImageBatchRequest(
            game_id=game_id,
            user_id=current_user.id,
            image_files=image_files
        )

        response = await use_case.execute(request)

        if not response.success:
            if "not found" in response.error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=response.error_message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=response.error_message
                )

        return BatchUploadResponse(
            batch_id=response.batch_id,
            total_images=len(files),
            uploaded_images=response.uploaded_images,
            status="pending",
            message=f"Batch créé avec succès - {response.uploaded_images} images uploadées",
            job_ids=response.job_ids or []
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}"
        )


@router.get(
    "/batches/{batch_id}/status",
    response_model=BatchStatusResponse,
    responses={
        200: {"description": "Batch processing status"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Batch not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get batch processing status",
    description="Get the current status and progress of batch processing with detailed ratios"
)
async def get_batch_processing_status(
        batch_id: UUID,
        current_user: User = Depends(get_current_user),
        use_case: GetBatchStatusUseCase = Depends(get_get_batch_status_use_case)
) -> BatchStatusResponse:
    """Récupère le statut détaillé de traitement d'un batch"""

    response = await use_case.execute(batch_id)

    if not response.success:
        if "not found" in response.error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error_message
            )

    batch = response.batch
    return BatchStatusResponse(
        batch_id=batch.id,
        status=batch.status.value,
        total_images=batch.total_images,
        processed_images=batch.processed_images,
        failed_images=batch.failed_images,
        progress_ratio=batch.progress_ratio,
        failed_ratio=batch.failed_ratio,
        completion_percentage=batch.completion_percentage,
        failure_percentage=batch.failure_percentage,
        can_retry=batch.can_retry(),
        retry_count=batch.retry_count,
        max_retries=batch.max_retries,
        progress_message=response.progress_message,
        created_at=batch.created_at.isoformat(),
        processing_started_at=batch.processing_started_at.isoformat() if batch.processing_started_at else None,
        completed_at=batch.completed_at.isoformat() if batch.completed_at else None
    )