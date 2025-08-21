from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# Engine asynchrone
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log des requêtes SQL en mode debug
    pool_pre_ping=True,   # Vérification connexion 
    pool_recycle=300      # Recyclage des connexions (5min)
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency pour FastAPI
async def get_db() -> AsyncSession:
    """Dependency qui fournit une session de base de données"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()