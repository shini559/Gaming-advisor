import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.adapters.database.connection import create_database_engine
from app.adapters.web.routes.auth import router as auth_router

# Create FastAPI app instance
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    debug=settings.debug,
    description="GameAdvisor API v2 - AI-powered board game assistant"
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


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    if settings.database_url:
        create_database_engine()
        print("✅ Database engine created")
    else:
        print("⚠️  No database configuration found. Database features will be unavailable.")


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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
