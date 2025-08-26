import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from app.config import settings
from app.data.connection import create_database_engine
from app.presentation.routes.auth import router as auth_router
from app.presentation.routes.games import router as games_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.database_url:
        create_database_engine()
        print("Database engine created")
    else:
        print("No database configuration found. Database features will be unavailable.")

    yield

    # Shutdown (si nécessaire)
    # await cleanup_function()

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





@app.get("/")
async def root():
    return {
        "message": "GameAdvisor API v2 is running!",
        "version": settings.api_version,
        "docs": "/docs",
        "auth_endpoints": {
            "register": "/auth/register",
            "login": "/auth/login",
            "profile": "/auth/me"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post(
      "/test-delay",
      status_code=status.HTTP_200_OK,
      summary="Endpoint fictif avec délai",
      description="Endpoint temporaire qui attend 3 secondes et renvoie un message"
)
async def test_delay_endpoint(message: str) -> dict:
  """Endpoint fictif pour test avec délai de 3 secondes"""
  # Attendre 3 secondes
  await asyncio.sleep(3)

  # Renvoyer une réponse fictive
  return {
      "status": "success",
      "received_message": message,
      "response": f"Votre message '{message}' a été traité après 3 secondes d'attente",
      "timestamp": "2025-08-26T12:10:00Z",
      "processing_time_seconds": 3
  }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )