"""
Système de logging debug centralisé pour le traitement d'images par batch

Ce module fournit un logging détaillé activé uniquement en mode debug 
pour tracer tous les points critiques du workflow de traitement d'images.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List
from uuid import UUID
from contextlib import contextmanager
from functools import wraps

from app.config import settings

class BatchProcessingLogger:
    """Logger spécialisé pour le debug du traitement par batch"""
    
    def __init__(self):
        self.logger = logging.getLogger("batch_processing_debug")
        
    def _should_log(self) -> bool:
        """Vérifie si le logging debug est activé"""
        return settings.debug
        
    def _get_timestamp(self) -> str:
        """Génère un timestamp pour les logs"""
        return datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    
    def _format_message(self, component: str, message: str, **kwargs) -> str:
        """Formate un message de log avec contexte"""
        timestamp = self._get_timestamp()
        context_str = ""
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context_str = f" [{', '.join(context_parts)}]"
        return f"[{timestamp}] [{component}] {message}{context_str}"
    
    # === ENDPOINT API ===
    def log_endpoint_request(self, game_id: UUID, user_id: UUID, file_count: int, filenames: List[str]):
        """Log de début de requête batch upload"""
        if not self._should_log():
            return
        msg = self._format_message(
            "API_ENDPOINT", 
            f"Batch upload request received",
            game_id=game_id, user_id=user_id, files=file_count
        )
        self.logger.info(msg)
        if filenames:
            filenames_str = ", ".join(filenames[:5])  # Premier 5 noms
            if len(filenames) > 5:
                filenames_str += f" ... (+{len(filenames) - 5} more)"
            self.logger.info(f"[API_ENDPOINT] Files: {filenames_str}")
    
    def log_endpoint_response(self, batch_id: UUID, success: bool, uploaded_count: int, error: str = None):
        """Log de réponse de l'endpoint"""
        if not self._should_log():
            return
        msg = self._format_message(
            "API_ENDPOINT",
            f"Batch upload response",
            batch_id=batch_id, success=success, uploaded=uploaded_count
        )
        self.logger.info(msg)
        if error:
            self.logger.error(f"[API_ENDPOINT] Error: {error}")
    
    # === USE CASE ===
    def log_usecase_start(self, batch_id: UUID, game_id: UUID, total_files: int):
        """Log de début du use case"""
        if not self._should_log():
            return
        msg = self._format_message(
            "USE_CASE",
            f"Starting batch creation",
            batch_id=batch_id, game_id=game_id, total_files=total_files
        )
        self.logger.info(msg)
    
    def log_usecase_file_processing(self, batch_id: UUID, filename: str, file_size: int, success: bool, error: str = None):
        """Log de traitement d'un fichier individuel"""
        if not self._should_log():
            return
        status = "SUCCESS" if success else "FAILED"
        msg = self._format_message(
            "USE_CASE",
            f"File processing {status}",
            batch_id=batch_id, filename=filename, size_kb=round(file_size/1024, 1)
        )
        self.logger.info(msg)
        if error:
            self.logger.error(f"[USE_CASE] File error: {error}")
    
    def log_usecase_jobs_creation(self, batch_id: UUID, jobs_created: int, jobs_failed: int):
        """Log de création des jobs Redis"""
        if not self._should_log():
            return
        msg = self._format_message(
            "USE_CASE",
            f"Redis jobs creation completed",
            batch_id=batch_id, created=jobs_created, failed=jobs_failed
        )
        self.logger.info(msg)
    
    def log_usecase_complete(self, batch_id: UUID, final_images: int, final_jobs: int):
        """Log de fin du use case"""
        if not self._should_log():
            return
        msg = self._format_message(
            "USE_CASE",
            f"Batch creation completed",
            batch_id=batch_id, images=final_images, jobs=final_jobs
        )
        self.logger.info(msg)
    
    # === REDIS QUEUE ===
    def log_redis_connection(self, status: str, error: str = None):
        """Log de statut de connexion Redis"""
        if not self._should_log():
            return
        msg = self._format_message("REDIS_QUEUE", f"Connection {status}")
        self.logger.info(msg)
        if error:
            self.logger.error(f"[REDIS_QUEUE] Connection error: {error}")
    
    def log_job_enqueue(self, job_id: str, image_id: UUID, batch_id: UUID = None):
        """Log d'ajout d'un job à la queue"""
        if not self._should_log():
            return
        msg = self._format_message(
            "REDIS_QUEUE",
            f"Job enqueued",
            job_id=job_id, image_id=image_id, batch_id=batch_id
        )
        self.logger.info(msg)
    
    def log_job_dequeue(self, job_id: str = None, image_id: UUID = None, timeout: bool = False):
        """Log de récupération d'un job de la queue"""
        if not self._should_log():
            return
        if timeout:
            msg = self._format_message("REDIS_QUEUE", "Dequeue timeout (normal)")
        elif job_id:
            msg = self._format_message(
                "REDIS_QUEUE",
                f"Job dequeued",
                job_id=job_id, image_id=image_id
            )
        else:
            msg = self._format_message("REDIS_QUEUE", "No job available")
        self.logger.info(msg)
    
    def log_job_status_change(self, job_id: str, old_status: str, new_status: str):
        """Log de changement de statut de job"""
        if not self._should_log():
            return
        msg = self._format_message(
            "REDIS_QUEUE",
            f"Job status change",
            job_id=job_id, from_status=old_status, to_status=new_status
        )
        self.logger.info(msg)
    
    def log_job_retry(self, job_id: str, retry_count: int, max_retries: int):
        """Log de tentative de retry d'un job"""
        if not self._should_log():
            return
        msg = self._format_message(
            "REDIS_QUEUE",
            f"Job retry",
            job_id=job_id, attempt=retry_count, max_attempts=max_retries
        )
        self.logger.info(msg)
    
    # === WORKER ===
    def log_worker_start(self):
        """Log de démarrage du worker"""
        if not self._should_log():
            return
        msg = self._format_message("WORKER", "Image processing worker started")
        self.logger.info(msg)
    
    def log_worker_stop(self):
        """Log d'arrêt du worker"""
        if not self._should_log():
            return
        msg = self._format_message("WORKER", "Image processing worker stopped")
        self.logger.info(msg)
    
    def log_worker_job_start(self, job_id: str, image_id: UUID, batch_id: UUID = None):
        """Log de début de traitement d'un job par le worker"""
        if not self._should_log():
            return
        msg = self._format_message(
            "WORKER",
            f"Starting job processing",
            job_id=job_id, image_id=image_id, batch_id=batch_id
        )
        self.logger.info(msg)
    
    def log_worker_job_complete(self, job_id: str, image_id: UUID, processing_time: float):
        """Log de fin de traitement d'un job par le worker"""
        if not self._should_log():
            return
        msg = self._format_message(
            "WORKER",
            f"Job completed",
            job_id=job_id, image_id=image_id, duration_sec=round(processing_time, 2)
        )
        self.logger.info(msg)
    
    def log_worker_job_error(self, job_id: str, image_id: UUID, error: str, will_retry: bool):
        """Log d'erreur de traitement d'un job"""
        if not self._should_log():
            return
        retry_status = "WILL_RETRY" if will_retry else "FINAL_FAILURE"
        msg = self._format_message(
            "WORKER",
            f"Job failed - {retry_status}",
            job_id=job_id, image_id=image_id
        )
        self.logger.error(msg)
        self.logger.error(f"[WORKER] Error details: {error}")
    
    def log_worker_loop_error(self, error: str):
        """Log d'erreur dans la boucle principale du worker"""
        if not self._should_log():
            return
        msg = self._format_message("WORKER", f"Worker loop error: {error}")
        self.logger.error(msg)
    
    # === AZURE SERVICES ===
    def log_blob_operation(self, operation: str, blob_path: str, size_bytes: int = None, success: bool = True, error: str = None):
        """Log d'opération Azure Blob Storage"""
        if not self._should_log():
            return
        status = "SUCCESS" if success else "FAILED"
        msg = self._format_message(
            "AZURE_BLOB",
            f"{operation} {status}",
            blob_path=blob_path, size_kb=round(size_bytes/1024, 1) if size_bytes else None
        )
        self.logger.info(msg)
        if error:
            self.logger.error(f"[AZURE_BLOB] Error: {error}")
    
    def log_ai_processing_start(self, image_id: UUID, filename: str):
        """Log de début de traitement IA"""
        if not self._should_log():
            return
        msg = self._format_message(
            "AZURE_AI",
            f"Starting AI processing",
            image_id=image_id, filename=filename
        )
        self.logger.info(msg)
    
    def log_ai_processing_result(self, image_id: UUID, success: bool, ocr_length: int = 0, desc_length: int = 0, labels_count: int = 0, error: str = None):
        """Log de résultat de traitement IA"""
        if not self._should_log():
            return
        status = "SUCCESS" if success else "FAILED"
        msg = self._format_message(
            "AZURE_AI",
            f"AI processing {status}",
            image_id=image_id, ocr_chars=ocr_length, desc_chars=desc_length, labels=labels_count
        )
        self.logger.info(msg)
        if error:
            self.logger.error(f"[AZURE_AI] Error: {error}")
    
    def log_embedding_generation(self, content_type: str, content_length: int, embedding_length: int, success: bool, error: str = None):
        """Log de génération d'embeddings"""
        if not self._should_log():
            return
        status = "SUCCESS" if success else "FAILED"
        msg = self._format_message(
            "AZURE_AI",
            f"Embedding generation {status}",
            type=content_type, content_chars=content_length, embedding_dim=embedding_length
        )
        self.logger.info(msg)
        if error:
            self.logger.error(f"[AZURE_AI] Embedding error: {error}")
    
    # === DATABASE ===
    def log_db_operation(self, operation: str, table: str, record_id: UUID = None, success: bool = True, error: str = None):
        """Log d'opération base de données"""
        if not self._should_log():
            return
        status = "SUCCESS" if success else "FAILED"
        msg = self._format_message(
            "DATABASE",
            f"{operation} {status}",
            table=table, id=record_id
        )
        self.logger.info(msg)
        if error:
            self.logger.error(f"[DATABASE] Error: {error}")
    
    def log_batch_update(self, batch_id: UUID, processed: int, failed: int, total: int, status: str):
        """Log de mise à jour d'un batch"""
        if not self._should_log():
            return
        progress_pct = round((processed + failed) / total * 100, 1) if total > 0 else 0
        msg = self._format_message(
            "BATCH_UPDATE",
            f"Batch progress update",
            batch_id=batch_id, processed=processed, failed=failed, total=total, 
            status=status, progress_pct=progress_pct
        )
        self.logger.info(msg)
    
    # === CONTEXT MANAGERS ===
    @contextmanager
    def time_operation(self, operation_name: str, **context):
        """Context manager pour mesurer le temps d'opération"""
        if not self._should_log():
            yield
            return
        
        start_time = datetime.now(timezone.utc)
        msg = self._format_message("TIMER", f"Starting {operation_name}", **context)
        self.logger.info(msg)
        
        try:
            yield
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            msg = self._format_message("TIMER", f"Completed {operation_name}", duration_sec=round(duration, 2), **context)
            self.logger.info(msg)
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            msg = self._format_message("TIMER", f"Failed {operation_name}", duration_sec=round(duration, 2), **context)
            self.logger.error(msg)
            raise

# Instance globale
debug_logger = BatchProcessingLogger()

# Décorateurs utilitaires
def log_function_call(component: str):
    """Décorateur pour logger les appels de fonction"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if debug_logger._should_log():
                func_name = func.__name__
                debug_logger.logger.info(f"[{component}] Calling {func_name}")
            try:
                result = await func(*args, **kwargs)
                if debug_logger._should_log():
                    debug_logger.logger.info(f"[{component}] {func_name} completed successfully")
                return result
            except Exception as e:
                if debug_logger._should_log():
                    debug_logger.logger.error(f"[{component}] {func_name} failed: {str(e)}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if debug_logger._should_log():
                func_name = func.__name__
                debug_logger.logger.info(f"[{component}] Calling {func_name}")
            try:
                result = func(*args, **kwargs)
                if debug_logger._should_log():
                    debug_logger.logger.info(f"[{component}] {func_name} completed successfully")
                return result
            except Exception as e:
                if debug_logger._should_log():
                    debug_logger.logger.error(f"[{component}] {func_name} failed: {str(e)}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator