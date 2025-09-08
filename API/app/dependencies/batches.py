from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.image_batch_repository import ImageBatchRepository
from app.dependencies import get_game_image_repository, get_game_repository
from app.dependencies.database import get_db_session
from app.dependencies.services import get_blob_storage_service, get_queue_service
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.repositories.image_batch_repository import IImageBatchRepository
from app.domain.use_cases.images.create_image_batch import CreateImageBatchUseCase
from app.domain.use_cases.images.get_batch_status import GetBatchStatusUseCase


def get_image_batch_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ImageBatchRepository:
    """Dependency injection pour ImageBatchRepository"""
    return ImageBatchRepository(session)


def get_create_image_batch_use_case(
    batch_repository: IImageBatchRepository = Depends(get_image_batch_repository),
    image_repository: IGameImageRepository = Depends(get_game_image_repository),
    game_repository: IGameRepository = Depends(get_game_repository),
    blob_service = Depends(get_blob_storage_service),
    queue_service = Depends(get_queue_service)
) -> CreateImageBatchUseCase:
    """Dependency injection pour CreateImageBatchUseCase"""
    return CreateImageBatchUseCase(
        batch_repository=batch_repository,
        image_repository=image_repository,
        game_repository=game_repository,
        blob_service=blob_service,
        queue_service=queue_service
    )


def get_get_batch_status_use_case(
    batch_repository: IImageBatchRepository = Depends(get_image_batch_repository),
    image_repository: IGameImageRepository = Depends(get_game_image_repository),
    game_repository: IGameRepository = Depends(get_game_repository)
) -> GetBatchStatusUseCase:
    """Dependency injection pour GetBatchStatusUseCase"""
    return GetBatchStatusUseCase(
        batch_repository=batch_repository,
        image_repository=image_repository,
        game_repository=game_repository
    )