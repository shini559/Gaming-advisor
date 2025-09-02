from dataclasses import dataclass
from typing import List, BinaryIO
from uuid import UUID
import logging

from app.config import settings
from app.domain.entities.image_batch import ImageBatch
from app.domain.entities.game_image import GameImage
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

            # Log de debug : informations sur les fichiers reçus
            if settings.debug:
                file_info = [(f, s) for f, _, s in request.image_files]
                logging.info(f"[BATCH_UPLOAD_DEBUG] Batch {batch.id} - Game: {request.game_id}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] Nombre de fichiers reçus: {len(request.image_files)}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] Détails fichiers: {file_info}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] User: {request.user_id}, Admin: {request.user_is_admin}")

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
                    if settings.debug:
                        logging.error(f"[BATCH_UPLOAD_DEBUG] Échec upload image '{filename}' (taille: {size} bytes)")
                        logging.error(f"[BATCH_UPLOAD_DEBUG] Erreur: {str(e)}")
                        logging.error(f"[BATCH_UPLOAD_DEBUG] Type d'erreur: {type(e).__name__}")
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
            total_initial = len(request.image_files)
            total_failed = total_initial - batch.total_images
            
            # Log de debug : résumé final
            if settings.debug:
                logging.info(f"[BATCH_UPLOAD_DEBUG] Résumé final - Batch {batch.id}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] Images initiales: {total_initial}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] Images uploadées: {len(uploaded_images)}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] Images échouées: {total_failed}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] Jobs Redis créés: {len(job_ids)}")
                logging.info(f"[BATCH_UPLOAD_DEBUG] Total images final dans batch: {batch.total_images}")

            if batch.total_images > 0:
                await self.batch_repository.update(batch)

                if settings.debug:
                    logging.info(f"[BATCH_UPLOAD_DEBUG] Batch {batch.id} - SUCCÈS")

                return CreateImageBatchResult(
                    success=True,
                    batch_id=batch.id,
                    uploaded_images=len(uploaded_images),
                    job_ids=job_ids
                )
            else:
                # Aucune image n'a pu être uploadée
                if settings.debug:
                    logging.error(f"[BATCH_UPLOAD_DEBUG] Batch {batch.id} - ÉCHEC TOTAL - Suppression du batch")
                    
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