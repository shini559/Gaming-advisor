from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.database.connection import get_async_session

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
  """Dependency pour injecter une session DB"""
  async for session in get_async_session():
      try:
          yield session
          await session.commit()
      except Exception:
          await session.rollback()
          raise