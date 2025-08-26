import pytest
import asyncio
from datetime import datetime, timezone

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event, DateTime as SQLDateTime, TypeDecorator

from app.dependencies import get_db_session
from app.main import app
from app.data.connection import Base


@pytest.fixture(scope="session")
def event_loop():
  """Create event loop for async tests"""
  loop = asyncio.get_event_loop_policy().new_event_loop()
  yield loop
  loop.close()


class TimezoneAwareDateTime(TypeDecorator):
    """Type DateTime qui force timezone UTC pour SQLite dans les tests"""
    impl = SQLDateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


@event.listens_for(Base.metadata, "before_create")
def receive_before_create(target, connection, **kw):
    for table in target.tables.values():
        for column in table.columns:
            if isinstance(column.type, SQLDateTime):
                column.type = TimezoneAwareDateTime()


@pytest_asyncio.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")  # Base en mémoire pour chaque test

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session):
  """Create test client with overridden dependencies"""
  app.dependency_overrides[get_db_session] = lambda: db_session

  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
      yield client

  app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
  """Fixture pour données utilisateur de test"""
  return {
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "password": "testpassword123"
  }

