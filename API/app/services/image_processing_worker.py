import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4
import traceback

from app.config import settings
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
from app.services.monitoring_service import monitoring_service
from app.services.structured_logger import image_logger

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
        """Démarre le worker"""
        self.running = True
        logger.info("Image processing worker started")

        while self.running:
            try:
                await self._process_next_job()
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)  # Pause en cas d'erreur

    async def stop(self) -> None:
        """Arrête le worker"""
        self.running = False
        await self.queue_service.close()
        await self.blob_service.close()
        logger.info("Image processing worker stopped")

    async def _process_next_job(self):
        """Traite la prochaine tâche dans la queue"""
        # Récupérer une tâche
        job = await self.queue_service.dequeue_job()
        if not job:
            if settings.debug:
                logger.info("[JOB_DEBUG] No job available, waiting...")
            return

        logger.info(f"Processing job {job.job_id} for image {job.image_id}")

        # Démarrer le timer pour le mode debug
        start_time = datetime.now(timezone.utc)

        try:
            # Marquer comme en cours de traitement
            if settings.debug:
                logger.info(f"[JOB_DEBUG] ÉTAPE 1/5: Marquage du job comme en cours...")
            await self.queue_service.mark_job_processing(job.job_id)
            if settings.debug:
                logger.info(f"[JOB_DEBUG] ÉTAPE 1/5: ✅ Job marqué comme en cours")
                logger.info(f"[JOB_DEBUG] ÉTAPE 2/5: Début du traitement de l'image...")
            # Traiter la tâche
            await self._process_image_job(job)
            if settings.debug:
                logger.info(f"[JOB_DEBUG] ÉTAPE 2/5: ✅ Traitement de l'image terminé")

            # Marquer comme terminé
            if settings.debug:
                logger.info(f"[JOB_DEBUG] ÉTAPE 3/5: Marquage du job comme terminé...")
            await self.queue_service.mark_job_completed(job.job_id)
            if settings.debug:
                end_time = datetime.now(timezone.utc)
                duration = (end_time - start_time).total_seconds()
                logger.info(f"[JOB_DEBUG] ÉTAPE 3/5: ✅ Job marqué comme terminé")
                logger.info(f"[JOB_DEBUG] SUCCÈS TOTAL en {duration:.2f}s")
                logger.info(f"[JOB_DEBUG] =====================================")
                # Pause pour permettre de suivre en mode debug
                await asyncio.sleep(2)

            logger.info(f"Job {job.job_id} completed successfully")

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            error_msg = f"Job {job.job_id} failed: {str(e)}"
            logger.error(error_msg)

            # === MODE DEBUG SÉQUENTIEL : Log détaillé d'erreur ===
            if settings.debug:
                logger.error(f"[JOB_DEBUG] ❌ ÉCHEC après {duration:.2f}s")
                logger.error(f"[JOB_DEBUG] Erreur: {str(e)}")
                logger.error(f"[JOB_DEBUG] Type d'erreur: {type(e).__name__}")
                logger.error(f"[JOB_DEBUG] Job ID: {job.job_id}")
                logger.error(f"[JOB_DEBUG] Image ID: {job.image_id}")
                logger.error(f"[JOB_DEBUG] Batch ID: {job.batch_id}")
                logger.error(f"[JOB_DEBUG] Stack trace:")
                logger.error(traceback.format_exc())
                logger.error(f"[JOB_DEBUG] =====================================")

            # Marquer comme échoué
            await self.queue_service.mark_job_failed(job.job_id, str(e))

            # Tenter un retry si possible
            if job.retry_count < job.max_retries:
                await self.queue_service.retry_failed_job(job.job_id)
                logger.info(f"Job {job.job_id} queued for retry ({job.retry_count + 1}/{job.max_retries})")
                if settings.debug:
                    logger.info(f"[JOB_DEBUG] Job en retry, continuons...")
            else:
                if settings.debug:
                    logger.error(f"[JOB_DEBUG] Job {job.job_id} - MAX RETRIES ATTEINT - ABANDON DÉFINITIF")

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
            ai_start = time.perf_counter()
            ai_result = await self.ai_service.process_image(image_content, job.filename)
            ai_latency = time.perf_counter() - ai_start
            logger.info(f"🤖 AI processing result: success={ai_result.success}")

            # Enregistrer le traitement d'image global
            monitoring_service.record_image_processing(
                latency=ai_latency,
                processing_type="full_pipeline",
                success=ai_result.success,
            )
            image_logger.image_processed(
                filename=job.filename,
                processing_type="full_pipeline",
                latency=ai_latency,
                success=ai_result.success,
            )

            if ai_result.success:
                # Architecture 3-paires : OCR, Description, Labels
                if ai_result.ocr_content:
                    logger.info(f"📝 OCR content: {ai_result.ocr_content[:100]}...")
                if ai_result.description_content:
                    logger.info(f"🖼️ Description: {ai_result.description_content[:100]}...")
                if ai_result.labels_content:
                    logger.info(f"🏷️ Labels: {ai_result.labels_content}")
                
                logger.info(f"🔢 OCR embedding length: {len(ai_result.ocr_embedding) if ai_result.ocr_embedding else 0}")
                logger.info(f"🔢 Description embedding length: {len(ai_result.description_embedding) if ai_result.description_embedding else 0}")
                logger.info(f"🔢 Labels embedding length: {len(ai_result.labels_embedding) if ai_result.labels_embedding else 0}")

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
            # Utiliser la méthode de l'interface
            content = await self.blob_service.download_image(blob_path)
            return BytesIO(content)

        except Exception as e:
            raise ValueError(f"Failed to download image from {blob_path}: {str(e)}")


    async def _save_vectors(self, job, ai_result) -> None:
        """Sauvegarde les vecteurs en base de données"""
        async with get_session() as session:
            vector_repo = self._vector_repository or GameVectorRepository(session)

            # === Architecture 3-paires : Un seul GameVector avec toutes les données ===
            # Plus de multiple entrées par image - une seule entrée avec toutes les paires
            
            vector = GameVector(
                id=uuid4(),
                game_id=job.game_id,
                image_id=job.image_id,
                
                # OCR (si disponible)
                ocr_content=ai_result.ocr_content,
                ocr_embedding=ai_result.ocr_embedding,
                
                # Description (si disponible)
                description_content=ai_result.description_content,
                description_embedding=ai_result.description_embedding,
                
                # Labels (si disponible)
                labels_content=ai_result.labels_content,
                labels_embedding=ai_result.labels_embedding,
                
                # Métadonnées
                page_number=1,  # Pourrait être extrait des métadonnées EXIF
                created_at=datetime.now(timezone.utc)
            )
            
            # Ne créer que si on a au moins un type de données
            if ai_result.has_any_data():
                await vector_repo.create(vector)
                logger.info(f"✅ Vecteur créé avec types: {', '.join(ai_result.get_extracted_types())}")
            else:
                logger.warning("⚠️ Aucune donnée extraite - pas de vecteur créé")

            await session.commit()

    async def _update_batch_progress(self, session, batch_id, success: bool):
        """Met à jour le progrès du batch après traitement d'une image"""
        if settings.debug:
            logging.info(f"[BATCH_PROGRESS_DEBUG] ===== DÉBUT MISE À JOUR BATCH =====")
            logging.info(f"[BATCH_PROGRESS_DEBUG] Batch ID: {batch_id}")
            logging.info(f"[BATCH_PROGRESS_DEBUG] Success: {success}")
        
        try:
            batch_repo = self._batch_repository or ImageBatchRepository(session)
            
            # Récupérer le batch
            batch = await batch_repo.get_by_id(batch_id)
            if not batch:
                if settings.debug:
                    logging.error(f"[BATCH_PROGRESS_DEBUG] ERREUR: Batch {batch_id} not found in database")
                logger.warning(f"Batch {batch_id} not found")
                return
            
            # Log de l'état AVANT mise à jour
            if settings.debug:
                logging.info(f"[BATCH_PROGRESS_DEBUG] État AVANT:")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Total images: {batch.total_images}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Processed images: {batch.processed_images}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Failed images: {batch.failed_images}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Status: {batch.status.value}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Progress ratio: {batch.progress_ratio}")
            
            # Mettre à jour les compteurs
            if success:
                batch.processed_images += 1
                if settings.debug:
                    logging.info(f"[BATCH_PROGRESS_DEBUG] Incrémentation processed_images: {batch.processed_images - 1} -> {batch.processed_images}")
            else:
                batch.failed_images += 1
                if settings.debug:
                    logging.info(f"[BATCH_PROGRESS_DEBUG] Incrémentation failed_images: {batch.failed_images - 1} -> {batch.failed_images}")
            
            # Calculer le nouveau statut
            total_processed = batch.processed_images + batch.failed_images
            
            if settings.debug:
                logging.info(f"[BATCH_PROGRESS_DEBUG] Total processed calculé: {total_processed}")
            
            # Gestion du changement de statut
            old_status = batch.status
            if batch.status == BatchStatus.PENDING:
                batch.status = BatchStatus.PROCESSING
                batch.processing_started_at = datetime.now(timezone.utc)
                if settings.debug:
                    logging.info(f"[BATCH_PROGRESS_DEBUG] Changement statut: PENDING -> PROCESSING")
            
            if total_processed >= batch.total_images:
                # Batch terminé
                batch.completed_at = datetime.now(timezone.utc)
                
                if batch.failed_images == 0:
                    batch.status = BatchStatus.COMPLETED
                    if settings.debug:
                        logging.info(f"[BATCH_PROGRESS_DEBUG] Changement statut: {old_status.value} -> COMPLETED (toutes réussies)")
                elif batch.processed_images == 0:
                    batch.status = BatchStatus.FAILED
                    if settings.debug:
                        logging.info(f"[BATCH_PROGRESS_DEBUG] Changement statut: {old_status.value} -> FAILED (toutes échouées)")
                else:
                    batch.status = BatchStatus.PARTIALLY_COMPLETED
                    if settings.debug:
                        logging.info(f"[BATCH_PROGRESS_DEBUG] Changement statut: {old_status.value} -> PARTIALLY_COMPLETED")
            
            # Log de l'état APRÈS mise à jour
            if settings.debug:
                logging.info(f"[BATCH_PROGRESS_DEBUG] État APRÈS:")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Total images: {batch.total_images}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Processed images: {batch.processed_images}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Failed images: {batch.failed_images}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Status: {batch.status.value}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Progress ratio: {batch.progress_ratio}")
                logging.info(f"[BATCH_PROGRESS_DEBUG] - Total processed: {total_processed}")
                
                # Test critique : est-ce que le batch est terminé ?
                if total_processed >= batch.total_images:
                    logging.info(f"[BATCH_PROGRESS_DEBUG] ✅ BATCH COMPLET: {total_processed}/{batch.total_images}")
                else:
                    logging.info(f"[BATCH_PROGRESS_DEBUG] 🔄 BATCH EN COURS: {total_processed}/{batch.total_images}")
            
            # Sauvegarder
            await batch_repo.update(batch)
            
            if settings.debug:
                logging.info(f"[BATCH_PROGRESS_DEBUG] ✅ Batch sauvegardé en base de données")
                logging.info(f"[BATCH_PROGRESS_DEBUG] ===== FIN MISE À JOUR BATCH =====")
            
            logger.info(f"Batch {batch_id} updated: {batch.progress_ratio} processed, status={batch.status.value}")
            
        except Exception as e:
            if settings.debug:
                logging.error(f"[BATCH_PROGRESS_DEBUG] ❌ ERREUR lors de la mise à jour du batch:")
                logging.error(f"[BATCH_PROGRESS_DEBUG] - Batch ID: {batch_id}")
                logging.error(f"[BATCH_PROGRESS_DEBUG] - Success: {success}")
                logging.error(f"[BATCH_PROGRESS_DEBUG] - Erreur: {str(e)}")
                logging.error(f"[BATCH_PROGRESS_DEBUG] - Type: {type(e).__name__}")
                import traceback
                logging.error(f"[BATCH_PROGRESS_DEBUG] Stack trace: {traceback.format_exc()}")
            raise