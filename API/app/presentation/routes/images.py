from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from starlette import status
from uuid import UUID
from typing import List
import logging

from app.config import settings
from app.dependencies import get_current_user
from app.shared.utils.debug_logger import debug_logger
from app.dependencies.batches import get_create_image_batch_use_case, get_get_batch_status_use_case
from app.domain.use_cases.images.create_image_batch import CreateImageBatchUseCase, CreateImageBatchRequest
from app.domain.use_cases.images.get_batch_status import GetBatchStatusUseCase
from app.presentation.schemas.images import BatchUploadResponse, BatchStatusResponse
from app.presentation.schemas.auth import ErrorResponse
from app.domain.entities.user import User


router = APIRouter(prefix="/images", tags=["Images"])




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

    # Log de debug : informations de la requête reçue
    if settings.debug:
        logging.info(f"[ENDPOINT_BATCH_DEBUG] Requête batch-upload reçue")
        logging.info(f"[ENDPOINT_BATCH_DEBUG] Game ID: {game_id}")
        logging.info(f"[ENDPOINT_BATCH_DEBUG] User: {current_user.id} (admin: {current_user.is_admin})")
        logging.info(f"[ENDPOINT_BATCH_DEBUG] Nombre de fichiers FastAPI: {len(files) if files else 0}")

        if files and settings.debug:
            filenames = [f.filename for f in files]
            logging.info(f"[ENDPOINT_BATCH_DEBUG] Noms des fichiers: {filenames}")
    
    try:
        # Validation des fichiers
        if not files:
            if settings.debug:
                logging.error("[ENDPOINT_BATCH_DEBUG] Aucun fichier fourni")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Au moins une image est requise"
            )

        # Préparer les fichiers pour le use case
        image_files = []
        for file in files:
            content = await file.read()
            image_files.append((file.filename or "unknown", content, len(content)))

        # Log de debug : fichiers préparés avant appel use case
        if settings.debug:
            sizes = [size for _, _, size in image_files]
            logging.info(f"[ENDPOINT_BATCH_DEBUG] Fichiers préparés: {len(image_files)}")
            logging.info(f"[ENDPOINT_BATCH_DEBUG] Tailles: {sizes}")

        request = CreateImageBatchRequest(
            game_id=game_id,
            user_id=current_user.id,
            image_files=image_files,
            user_is_admin=current_user.is_admin
        )

        if settings.debug:
            logging.info(f"[ENDPOINT_BATCH_DEBUG] Appel du use case...")

        response = await use_case.execute(request)

        # Log de debug : réponse du use case
        if settings.debug:
            logging.info(f"[ENDPOINT_BATCH_DEBUG] Réponse use case - Success: {response.success}")
            if response.success:
                logging.info(f"[ENDPOINT_BATCH_DEBUG] Batch ID: {response.batch_id}")
                logging.info(f"[ENDPOINT_BATCH_DEBUG] Images uploadées: {response.uploaded_images}")
                logging.info(f"[ENDPOINT_BATCH_DEBUG] Jobs créés: {len(response.job_ids) if response.job_ids else 0}")
            else:
                logging.error(f"[ENDPOINT_BATCH_DEBUG] Erreur: {response.error_message}")

        if not response.success:
            if "not found" in response.error_message.lower():
                if settings.debug:
                    logging.error(f"[ENDPOINT_BATCH_DEBUG] Retour HTTP 404: {response.error_message}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=response.error_message
                )
            else:
                if settings.debug:
                    logging.error(f"[ENDPOINT_BATCH_DEBUG] Retour HTTP 400: {response.error_message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=response.error_message
                )

        if settings.debug:
           logging.info(f"[ENDPOINT_BATCH_DEBUG] Succès - Retour HTTP 202")

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
        if settings.debug:
            logging.error(f"[ENDPOINT_BATCH_DEBUG] Exception inattendue: {str(e)}")
            logging.error(f"[ENDPOINT_BATCH_DEBUG] Type: {type(e).__name__}")
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

    response = await use_case.execute(batch_id, current_user.id, current_user.is_admin)

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