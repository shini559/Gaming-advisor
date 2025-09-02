from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from app.config import settings
from app.data.connection import create_database_engine
from app.dependencies import get_queue_service, get_blob_storage_service
from app.dependencies.images import get_start_processing_worker_use_case, get_ai_processing_service
from app.domain.use_cases.images.start_processing_worker import StartProcessingWorkerUseCase
from app.presentation.routes.auth import router as auth_router
from app.presentation.routes.games import router as games_router
from app.presentation.routes.images import router as images_router
from app.presentation.routes.chat import router as chat_router
from app.services.blob_storage_service import AzureBlobStorageService
from app.services.openai_processing_service import OpenAIProcessingService
from app.services.redis_queue_service import RedisQueueService


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== LIFESPAN START ===")

    # Startup
    if settings.database_url:
        create_database_engine()
        print("Database engine created")
    else:
        print("No database configuration found. Database features will be unavailable.")

    print("About to start worker setup...")
    logger.info("🚀 Starting GameAdvisor API v2...")
    worker_use_case = None

    try:
        print("Creating services...")
        # Créer les services singletons
        queue_service = RedisQueueService()
        print("✅ RedisQueueService created")

        blob_service = AzureBlobStorageService()
        print("✅ AzureBlobStorageService created")

        ai_service = OpenAIProcessingService()
        print("✅ OpenAIProcessingService created")

        print("Creating worker use case...")
        worker_use_case = StartProcessingWorkerUseCase(
            queue_service=queue_service,
            blob_service=blob_service,
            ai_service=ai_service,
            image_repository=None,
            vector_repository=None
        )
        print("✅ Worker use case created")

        print("Starting worker...")
        # Démarrer le worker
        result = await worker_use_case.execute()

        if result.success:
            logger.info("✅ Image processing worker started")
            print("✅ Image processing worker started")
        else:
            logger.error(f"❌ Failed to start worker: {result.message}")
            print(f"❌ Failed to start worker: {result.message}")

    except Exception as e:
        logger.error(f"💥 Startup error: {e}")
        print(f"💥 Startup error: {e}")
        import traceback
        traceback.print_exc()

    print("=== LIFESPAN YIELD ===")
    yield

    # Shutdown
    print("=== LIFESPAN SHUTDOWN ===")
    logger.info("🛑 Shutting down GameAdvisor API v2...")
    if worker_use_case:
        await worker_use_case.stop()
        logger.info("✅ Image processing worker stopped")


# Create FastAPI app instance
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    description="GameAdvisor API - AI-powered board game assistant",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(games_router)
app.include_router(images_router)
app.include_router(chat_router)


@app.get("/")
async def root() -> dict:
    return {
        "message": "GameAdvisor API is running!",
        "version": settings.api_version,
        "docs": "/docs",
        "auth_endpoints": {
            "register": "/auth/register",
            "login": "/auth/login",
            "profile": "/auth/me"
        },
        "images": {
            "upload": "/images/games/{game_id}/upload",
            "status": "/images/{image_id}/status"
        },
        "chat": {
            "create_conversation": "/chat/conversations",
            "send_message": "/chat/messages",
            "get_history": "/chat/conversations/{conversation_id}/history",
            "add_feedback": "/chat/messages/{message_id}/feedback"
        }
    }


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}





if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )