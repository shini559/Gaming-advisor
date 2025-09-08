from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from app.config import settings

# Base class for all SQLAlchemy models
Base = declarative_base()

# Create async engine
engine = None
async_session_factory = None

def create_database_engine() -> None:
    """Create database engine and session factory"""
    global engine, async_session_factory
    
    if not settings.database_url:
        raise ValueError("Database URL not configured. Please set DB_HOST, DB_USERNAME, DB_PASSWORD, and DB_NAME in your .env file.")
    
    engine = create_async_engine(
        settings.database_url,
        echo=settings.sql_debug,  # Log SQL queries seulement si sql_debug activé
        future=True,
        pool_pre_ping=True,  # Verify connections before use
    )
    
    async_session_factory = async_sessionmaker(
        engine, 
        class_=AsyncSession,
        expire_on_commit=False
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    if async_session_factory is None:
        create_database_engine()

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize database - create tables"""
    if not engine:
        create_database_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Close database connections"""
    global engine
    if engine:
        await engine.dispose()
        engine = None