from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.entities.image_batch import ImageBatch
from app.domain.ports.repositories.image_batch_repository import IImageBatchRepository
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_repository import IGameRepository


@dataclass 
class GetBatchStatusResult:
    """Résultat du statut de batch avec détails de progression"""
    success: bool
    batch: Optional[ImageBatch] = None
    progress_message: Optional[str] = None
    error_message: Optional[str] = None


class GetBatchStatusUseCase:
    """Use case pour récupérer le statut détaillé d'un batch"""

    def __init__(
        self,
        batch_repository: IImageBatchRepository,
        image_repository: IGameImageRepository,
        game_repository: IGameRepository
    ):
        self.batch_repository = batch_repository
        self.image_repository = image_repository
        self.game_repository = game_repository

    async def execute(self, batch_id: UUID, user_id: UUID, user_is_admin: bool = False) -> GetBatchStatusResult:
        """Récupérer le statut détaillé d'un batch"""
        
        try:
            # 1. Récupérer le batch
            batch = await self.batch_repository.get_by_id(batch_id)
            if not batch:
                return GetBatchStatusResult(
                    success=False,
                    error_message=f"Batch {batch_id} non trouvé"
                )
            
            # 2. SÉCURITÉ: Vérifier que l'utilisateur peut accéder à ce batch
            game = await self.game_repository.get_by_id(batch.game_id)
            if not game:
                return GetBatchStatusResult(
                    success=False,
                    error_message=f"Jeu associé au batch non trouvé"
                )
            
            if not self._can_user_access_batch(game, user_id, user_is_admin):
                return GetBatchStatusResult(
                    success=False,
                    error_message="Accès refusé : vous ne pouvez consulter que vos propres batch ou les batch de jeux publics (admin)"
                )

            # 3. Construire le message de progression selon le statut
            progress_message = self._build_progress_message(batch)

            return GetBatchStatusResult(
                success=True,
                batch=batch,
                progress_message=progress_message
            )

        except Exception as e:
            return GetBatchStatusResult(
                success=False,
                error_message=f"Erreur lors de la récupération du statut : {str(e)}"
            )

    def _build_progress_message(self, batch: ImageBatch) -> str:
        """Construire le message de progression selon le statut et les ratios"""
        
        if batch.status.value == "pending":
            return f"En attente - {batch.total_images} images à traiter"
        
        elif batch.status.value == "processing":
            return f"En cours - {batch.progress_ratio} images traitées"
        
        elif batch.status.value == "retrying":
            return f"Nouvel essai en cours - {batch.progress_ratio} images traitées, {batch.failed_ratio} en échec (tentative {batch.retry_count}/{batch.max_retries})"
        
        elif batch.status.value == "completed":
            return f"Terminé - {batch.progress_ratio} images traitées avec succès"
        
        elif batch.status.value == "partially_completed":
            return f"Terminé partiellement - {batch.progress_ratio} images traitées, {batch.failed_ratio} échecs définitifs"
        
        elif batch.status.value == "failed":
            return f"Échec - {batch.failed_ratio} images ont échoué après {batch.retry_count} tentatives"
        
        else:
            return f"Statut inconnu - {batch.progress_ratio} images traitées"
    
    def _can_user_access_batch(self, game, user_id: UUID, user_is_admin: bool) -> bool:
        """Vérifie si l'utilisateur peut accéder au statut de ce batch"""
        # 1. Propriétaire du jeu : toujours autorisé
        if game.created_by == user_id:
            return True
        
        # 2. Admin sur jeu public : autorisé
        if user_is_admin and game.is_public:
            return True
            
        # 3. Autres cas : refusé
        return False