from dataclasses import dataclass
from typing import List, BinaryIO
from uuid import UUID

from app.config import settings
from app.domain.entities.image_batch import ImageBatch
from app.domain.entities.game_image import GameImage, ImageProcessingStatus
from app.domain.ports.repositories.image_batch_repository import IImageBatchRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_repository import IGameRepository
from app.domain.ports.services.blob_storage_service import IBlobStorageService
from app.domain.ports.services.queue_service import IQueueService


@dataclass
class CreateImageBatchRequest:
    """Request pour créer un batch d'images"""
    game_id: UUID
    user_id: UUID
    image_files: List[tuple[str, BinaryIO, int]]  # (filename, content, size)
    user_is_admin: bool = False  # Privilèges admin pour upload


@dataclass
class CreateImageBatchResult:
    """Résultat de création de batch d'images"""
    success: bool
    batch_id: UUID | None = None
    uploaded_images: int = 0
    error_message: str | None = None
    job_ids: List[str] | None = None


class CreateImageBatchUseCase:
    """Use case pour créer un batch d'images"""

    def __init__(
        self,
        batch_repository: IImageBatchRepository,
        image_repository: IGameImageRepository,
        game_repository: IGameRepository,
        blob_service: IBlobStorageService,
        queue_service: IQueueService
    ):
        self.batch_repository = batch_repository
        self.image_repository = image_repository
        self.game_repository = game_repository
        self.blob_service = blob_service
        self.queue_service = queue_service

    async def execute(self, request: CreateImageBatchRequest) -> CreateImageBatchResult:
        """Créer un batch d'images et les uploader"""
        try:
            # 1. Vérifier que le jeu existe
            game = await self.game_repository.get_by_id(request.game_id)
            if not game:
                return CreateImageBatchResult(
                    success=False,
                    error_message=f"Jeu {request.game_id} non trouvé"
                )
            
            # 2. SÉCURITÉ: Vérifier que l'utilisateur peut uploader sur ce jeu
            if not self._can_user_upload_to_game(game, request.user_id, request.user_is_admin):
                return CreateImageBatchResult(
                    success=False,
                    error_message="Accès refusé : vous ne pouvez uploader que sur vos propres jeux ou les jeux publics (admin)"
                )

            if not request.image_files:
                return CreateImageBatchResult(
                    success=False,
                    error_message="Aucune image fournie"
                )

            # 2. Créer le batch
            batch = ImageBatch.create(
                game_id=request.game_id,
                total_images=len(request.image_files),
                max_retries=settings.batch_max_retries
            )
            
            saved_batch = await self.batch_repository.create(batch)

            # 3. Uploader les images en parallèle et créer les entités GameImage
            uploaded_images = []
            job_ids = []

            for filename, content, size in request.image_files:
                try:
                    # Créer d'abord l'entité GameImage pour avoir l'image_id
                    image_entity = GameImage.create(
                        game_id=request.game_id,
                        file_path="",  # Temporaire, sera mis à jour après upload
                        blob_url="",   # Temporaire, sera mis à jour après upload
                        original_filename=filename,
                        file_size=size,
                        uploaded_by=request.user_id,
                        batch_id=batch.id
                    )
                    
                    # Upload vers Azure Blob avec la vraie méthode
                    from io import BytesIO
                    file_path, blob_url = await self.blob_service.upload_image(
                        game_id=request.game_id,
                        image_id=image_entity.id,
                        file_content=BytesIO(content),
                        filename=filename,
                        content_type="image/jpeg"
                    )
                    
                    # Mettre à jour l'entité avec les vraies valeurs
                    image_entity.file_path = file_path
                    image_entity.blob_url = blob_url
                    
                    # Sauvegarder en base
                    saved_image = await self.image_repository.create(image_entity)
                    uploaded_images.append(saved_image)

                except Exception as e:
                    # Si une image échoue, on continue avec les autres
                    batch.total_images -= 1
                    continue

            # 4. Créer tous les jobs Redis après avoir sauvegardé toutes les images
            for saved_image in uploaded_images:
                try:
                    job_id = await self.queue_service.enqueue_image_processing(
                        image_id=saved_image.id,
                        game_id=request.game_id,
                        blob_path=saved_image.file_path,
                        filename=saved_image.original_filename,
                        batch_id=batch.id  # Associer le job au batch
                    )
                    job_ids.append(job_id)
                except Exception as e:
                    # Si la création du job échoue, on continue sans affecter les autres
                    continue

            # 5. Mettre à jour le batch avec le nombre final d'images
            if batch.total_images > 0:
                await self.batch_repository.update(batch)

                return CreateImageBatchResult(
                    success=True,
                    batch_id=batch.id,
                    uploaded_images=len(uploaded_images),
                    job_ids=job_ids
                )
            else:
                # Aucune image n'a pu être uploadée
                await self.batch_repository.delete(batch.id)
                return CreateImageBatchResult(
                    success=False,
                    error_message="Aucune image n'a pu être uploadée"
                )

        except Exception as e:
            return CreateImageBatchResult(
                success=False,
                error_message=f"Erreur lors de la création du batch : {str(e)}"
            )
    
    def _can_user_upload_to_game(self, game, user_id: UUID, user_is_admin: bool) -> bool:
        """Vérifie si l'utilisateur peut uploader des images pour ce jeu"""
        # 1. Propriétaire du jeu : toujours autorisé
        if game.created_by == user_id:
            return True
        
        # 2. Admin sur jeu public : autorisé
        if user_is_admin and game.is_public:
            return True
            
        # 3. Autres cas : refusé
        return False