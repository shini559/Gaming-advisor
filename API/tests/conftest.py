import pytest
import asyncio
from datetime import datetime, timezone

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event, DateTime as SQLDateTime, TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.dependencies import get_db_session
from app.dependencies.services import get_blob_storage_service, get_ai_processing_service, get_queue_service
from app.main import app
from app.data.connection import Base


# Mock des services Azure pour les tests
class MockAzureBlobStorageService:
    """Mock d'Azure Blob Storage pour les tests"""
    
    async def upload_image(self, game_id, image_id, file_content, filename: str, content_type: str) -> tuple[str, str]:
        file_path = f"games/{game_id}/images/{image_id}/{filename}"
        blob_url = f"https://mock-storage.blob.core.windows.net/gameadvisorstorage/{file_path}"
        return file_path, blob_url
    
    async def delete_image(self, file_path: str) -> bool:
        return True
    
    async def get_image_url(self, file_path: str, expires_in_hours: int = 24) -> str:
        return f"https://mock-storage.blob.core.windows.net/gameadvisorstorage/{file_path}?signed=true"

class MockOpenAIProcessingService:
    """Mock d'OpenAI Processing pour les tests"""
    def __init__(self):
        pass
    
    async def process_image(self, image_data: bytes, filename: str) -> dict: # Simuler traitement
        return {
            "ocr_text": "Mock OCR text from image",
            "description": "Mock description of game components",
            "labels": ["mock_component", "test_element"],
            "embedding": [0.1] * 1536  # Mock embedding vector
        }

class MockRedisQueueService:
    """Mock de Redis Queue pour les tests"""
    def __init__(self):
        self.jobs = {}
    
    async def enqueue_image_processing(self, image_id, game_id, blob_path: str, filename: str, batch_id=None) -> str:
        job_id = f"mock_job_{len(self.jobs)}"
        self.jobs[job_id] = {
            "status": "completed", 
            "image_id": str(image_id),
            "game_id": str(game_id),
            "blob_path": blob_path,
            "filename": filename,
            "batch_id": str(batch_id) if batch_id else None
        }
        return job_id
    
    async def get_job_status(self, job_id: str) -> dict:
        return self.jobs.get(job_id, {"status": "not_found"})


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
            # Remplacer JSONB par JSON pour SQLite
            elif isinstance(column.type, JSONB):
                column.type = JSON()


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
async def mock_azure_services():
    """Override les services Azure avec des mocks pour les tests"""
    
    # Créer les instances mock comme singletons
    mock_blob_service = MockAzureBlobStorageService()
    mock_ai_service = MockOpenAIProcessingService()
    mock_queue_service = MockRedisQueueService()
    
    # Fonctions de factory qui retournent directement les instances (évite les AsyncMock)
    def get_mock_blob_service():
        return mock_blob_service
    
    def get_mock_ai_service():
        return mock_ai_service
        
    def get_mock_queue_service():
        return mock_queue_service
    
    # Override les dépendances avec des fonctions normales
    app.dependency_overrides[get_blob_storage_service] = get_mock_blob_service
    app.dependency_overrides[get_ai_processing_service] = get_mock_ai_service
    app.dependency_overrides[get_queue_service] = get_mock_queue_service
    
    yield {
        "blob_service": mock_blob_service,
        "ai_service": mock_ai_service,
        "queue_service": mock_queue_service
    }
    
    # Cleanup après les tests
    if get_blob_storage_service in app.dependency_overrides:
        del app.dependency_overrides[get_blob_storage_service]
    if get_ai_processing_service in app.dependency_overrides:
        del app.dependency_overrides[get_ai_processing_service]
    if get_queue_service in app.dependency_overrides:
        del app.dependency_overrides[get_queue_service]


@pytest_asyncio.fixture
async def async_client(db_session, mock_azure_services):
  """Create test client with overridden dependencies"""
  
  # Override correct pour un générateur async
  async def override_get_db_session():
      yield db_session
  
  app.dependency_overrides[get_db_session] = override_get_db_session

  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
      yield client

  app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> dict:
  """Fixture pour données utilisateur de test"""
  return {
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "password": "testpassword123"
  }


class ClientHelper:
    """Classe utilitaire pour les tests d'intégration avec méthodes helper"""
    
    def __init__(self, client: AsyncClient, db_session: AsyncSession = None):
        self.client = client
        self.db_session = db_session
        self._user_counter = 0
    
    async def create_test_user(self, email: str, password: str = "testpass123", is_admin: bool = False) -> dict:
        """Créer un utilisateur de test"""
        self._user_counter += 1
        username = f"testuser{self._user_counter}"
        
        user_data = {
            "username": username,
            "email": email,
            "first_name": "Test",
            "last_name": f"User{self._user_counter}",
            "password": password
        }
        
        response = await self.client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        user_result = response.json()
        
        # Si admin requis, mettre à jour via la base de données directement
        if is_admin and self.db_session:
            # IMPORTANT: Commit la création d'utilisateur d'abord
            await self.db_session.commit()
            from sqlalchemy import text
            
            # CORRECTION: Convertir UUID avec hyphens vers UUID sans hyphens pour la base
            user_id_no_hyphens = user_result['user_id'].replace('-', '')
            
            # Mettre à jour le statut admin
            result = await self.db_session.execute(
                text("UPDATE users SET is_admin = 1 WHERE id = :user_id"),
                {"user_id": user_id_no_hyphens}
            )
            
            # Force commit (important pour les tests)
            await self.db_session.commit()
            
            # Note: Le token devra être regénéré après login pour refléter le statut admin
        
        return user_result  # UserResponse directe, pas dans un wrapper "user"
    
    async def login_user(self, email: str, password: str) -> str:
        """Connecter un utilisateur et retourner le token"""
        print(f"Tentative login pour: {email}")
        
        login_data = {
            "username": email,  # L'API utilise email comme username
            "password": password
        }
        
        # OAuth2PasswordRequestForm attend du form data, pas du JSON
        response = await self.client.post("/auth/login", data=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Login failed: {response.json()}")
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        print(f"Token généré: {token[:50]}...")
        return token
    
    async def create_test_game(self, title: str, is_public: bool = False, token: str = None) -> dict:
        """Créer un jeu de test (doit être connecté au préalable)"""
        game_data = {
            "title": title,
            "description": f"Description pour {title}",
            "publisher": "Test Publisher"
        }
        
        # Si jeu public demandé, l'ajouter dans les données
        if is_public:
            game_data["is_public"] = True
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = await self.client.post("/games/create", json=game_data, headers=headers)
        
        print(f"Tentative création jeu: {title} (is_public={is_public})")
        
        # Debug si erreur
        if response.status_code != 201:
            print(f"Game creation failed: {response.status_code}")
            print(f"Response: {response.json()}")
        else:
            print(f"Game created successfully")
            
        assert response.status_code == 201
        game_response = response.json()
        
        # Wrapper pour correspondre au format attendu par les tests
        return {"game": game_response}
    


@pytest_asyncio.fixture
async def test_client(async_client: AsyncClient, db_session: AsyncSession, mock_azure_services):
    """Fixture pour ClientHelper avec méthodes utilitaires"""
    yield ClientHelper(async_client, db_session)

