import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

from app.data.repositories.game_image_repository import GameImageRepository
from app.data.repositories.game_vector_repository import GameVectorRepository
from app.data.repositories.image_batch_repository import ImageBatchRepository
from app.dependencies.database import get_db_session
from app.domain.entities.game_image import ImageProcessingStatus
from app.domain.entities.game_vector import GameVector
from app.domain.entities.image_batch import BatchStatus
from app.domain.ports.repositories.game_image_repository import IGameImageRepository
from app.domain.ports.repositories.game_vector_repository import IGameVectorRepository
from app.domain.ports.repositories.image_batch_repository import IImageBatchRepository
from app.domain.ports.services.ai_processing_service import IAIProcessingService
from app.domain.ports.services.blob_storage_service import IBlobStorageService
from app.domain.ports.services.queue_service import IQueueService

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_session():
    session_gen = get_db_session()
    session = await session_gen.__anext__()
    try:
        yield session
    finally:
        await session.close()

class ImageProcessingWorker:
    """Worker qui traite les tâches d'images de manière asynchrone"""

    def __init__(
            self,
            queue_service: IQueueService,
            blob_service: IBlobStorageService,
            ai_service: IAIProcessingService,
            image_repository: IGameImageRepository = None,
            vector_repository: IGameVectorRepository = None,
            batch_repository: IImageBatchRepository = None
    ):
        self.queue_service = queue_service
        self.blob_service = blob_service
        self.ai_service = ai_service
        self._image_repository = image_repository
        self._vector_repository = vector_repository
        self._batch_repository = batch_repository
        self.running = False



    async def start(self):
        """Démarre le worker en mode continu"""
        self.running = True
        logger.info("Image processing worker started")

        while self.running:
            try:
                await self._process_next_job()
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)  # Pause en cas d'erreur

    async def stop(self) -> None:
        """Arrête le worker proprement"""
        self.running = False
        await self.queue_service.close()
        await self.blob_service.close()
        logger.info("Image processing worker stopped")

    async def _process_next_job(self):
        """Traite la prochaine tâche dans la queue"""
        # Récupérer une tâche
        job = await self.queue_service.dequeue_job()
        if not job:
            return

        logger.info(f"Processing job {job.job_id} for image {job.image_id}")

        try:
            # Marquer comme en cours de traitement
            await self.queue_service.mark_job_processing(job.job_id)

            # Traiter la tâche
            await self._process_image_job(job)

            # Marquer comme terminé
            await self.queue_service.mark_job_completed(job.job_id)
            logger.info(f"Job {job.job_id} completed successfully")

        except Exception as e:
            error_msg = f"Job {job.job_id} failed: {str(e)}"
            logger.error(error_msg)

            # Marquer comme échoué
            await self.queue_service.mark_job_failed(job.job_id, str(e))

            # Tenter un retry si possible
            if job.retry_count < job.max_retries:
                await self.queue_service.retry_failed_job(job.job_id)
                logger.info(f"Job {job.job_id} queued for retry ({job.retry_count + 1}/{job.max_retries})")

    async def _process_image_job(self, job):
        """Traite une tâche d'image spécifique"""
        # 1. Mettre à jour le statut en base
        async with get_session() as session:
            image_repo = self._image_repository or GameImageRepository(session)

            # Récupérer l'image
            image = await image_repo.get_by_id(job.image_id)
            if not image:
                raise ValueError(f"Image {job.image_id} not found")

            # Marquer comme en cours de traitement
            image.processing_status = ImageProcessingStatus.PROCESSING
            image.processing_started_at = datetime.now(timezone.utc)
            image.retry_count = job.retry_count
            await image_repo.update(image)
            await session.commit()

        try:
            # 2. Télécharger l'image depuis Azure Blob
            logger.info(f"🔽 Downloading image from {job.blob_path}")
            image_content = await self._download_image(job.blob_path)
            logger.info(f"✅ Downloaded {len(image_content.getvalue())} bytes")

            # 3. Traitement IA
            logger.info("🤖 Starting AI processing...")
            ai_result = await self.ai_service.process_image(image_content, job.filename)
            logger.info(f"🤖 AI processing result: success={ai_result.success}")

            if ai_result.success:
                logger.info(f"📝 Extracted text: {ai_result.extracted_text[:100]}...")
                logger.info(f"🖼️ Description: {ai_result.visual_description[:100]}...")
                logger.info(f"🏷️ Labels: {ai_result.labels}")
                logger.info(
                    f"🔢 Text embedding length: {len(ai_result.text_embedding) if ai_result.text_embedding else 0}")
                logger.info(
                    f"🔢 Desc embedding length: {len(ai_result.description_embedding) if ai_result.description_embedding else 0}")

            if not ai_result.success:
                raise ValueError(ai_result.error_message or "AI processing failed")

            # 4. Sauvegarder les vecteurs en base
            logger.info("💾 Saving vectors to database...")
            await self._save_vectors(job, ai_result)
            logger.info("✅ Vectors saved successfully")

            # 5. Marquer l'image comme terminée et mettre à jour le batch
            logger.info("✅ Marking image as completed and updating batch")

            async with get_session() as session:
                    image_repo = GameImageRepository(session)
                    image = await image_repo.get_by_id(job.image_id)

                    image.processing_status = ImageProcessingStatus.COMPLETED
                    image.processing_completed_at = datetime.now(timezone.utc)
                    image.processing_error = None

                    await image_repo.update(image)
                    
                    # Mettre à jour le batch
                    if image.batch_id:
                        await self._update_batch_progress(session, image.batch_id, success=True)
                    
                    await session.commit()

        except Exception as e:
            # Marquer l'image comme échouée et mettre à jour le batch
            async with get_session() as session:
                image_repo = GameImageRepository(session)
                image = await image_repo.get_by_id(job.image_id)

                image.processing_status = ImageProcessingStatus.FAILED
                image.processing_error = str(e)
                image.retry_count = job.retry_count

                await image_repo.update(image)
                
                # Mettre à jour le batch
                if image.batch_id:
                    await self._update_batch_progress(session, image.batch_id, success=False)
                
                await session.commit()

            raise

    async def _download_image(self, blob_path: str) -> BytesIO:
        """Télécharge une image depuis Azure Blob Storage"""
        try:
            from app.config import settings

            # Obtenir le container client
            container_client = self.blob_service.client.get_container_client(
                settings.azure_blob_container_name
            )
            blob_client = container_client.get_blob_client(blob_path)

            # Télécharger le contenu
            download_stream = await blob_client.download_blob()
            content = await download_stream.readall()

            return BytesIO(content)

        except Exception as e:
            raise ValueError(f"Failed to download image from {blob_path}: {str(e)}")


    async def _save_vectors(self, job, ai_result) -> None:
        """Sauvegarde les vecteurs en base de données"""
        async with get_session() as session:
            vector_repo = self._vector_repository or GameVectorRepository(session)

            # Créer le vecteur pour le texte extrait
            if ai_result.extracted_text and ai_result.text_embedding:
                text_vector = GameVector(
                    id=uuid4(),
                    game_id=job.game_id,
                    image_id=job.image_id,
                    vector_embedding=ai_result.text_embedding,
                    extracted_text=ai_result.extracted_text,
                    page_number=1,  # Pourrait être extrait des métadonnées
                    created_at=datetime.now(timezone.utc)
                )
                await vector_repo.create(text_vector)

            # Créer le vecteur pour la description
            if ai_result.visual_description and ai_result.description_embedding:
                desc_vector = GameVector(
                    id=uuid4(),
                    game_id=job.game_id,
                    image_id=job.image_id,
                    vector_embedding=ai_result.description_embedding,
                    extracted_text=f"Description: {ai_result.visual_description}\nLabels: {', '.join(ai_result.labels)}",
                    page_number=1,
                    created_at=datetime.now(timezone.utc)
                )
                await vector_repo.create(desc_vector)

            await session.commit()

    async def _update_batch_progress(self, session, batch_id, success: bool):
        """Met à jour le progrès du batch après traitement d'une image"""
        batch_repo = self._batch_repository or ImageBatchRepository(session)
        
        # Récupérer le batch
        batch = await batch_repo.get_by_id(batch_id)
        if not batch:
            logger.warning(f"Batch {batch_id} not found")
            return
        
        # Mettre à jour les compteurs
        if success:
            batch.processed_images += 1
        else:
            batch.failed_images += 1
        
        # Calculer le nouveau statut
        total_processed = batch.processed_images + batch.failed_images
        
        if batch.status == BatchStatus.PENDING:
            batch.status = BatchStatus.PROCESSING
            batch.processing_started_at = datetime.now(timezone.utc)
        
        if total_processed >= batch.total_images:
            # Batch terminé
            batch.completed_at = datetime.now(timezone.utc)
            
            if batch.failed_images == 0:
                batch.status = BatchStatus.COMPLETED
            elif batch.processed_images == 0:
                batch.status = BatchStatus.FAILED
            else:
                batch.status = BatchStatus.PARTIALLY_COMPLETED
        
        # Sauvegarder
        await batch_repo.update(batch)
        logger.info(f"Batch {batch_id} updated: {batch.progress_ratio} processed, status={batch.status.value}")