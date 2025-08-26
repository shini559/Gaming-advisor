# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GameAdvisor API v2** - Complete rewrite of the GameAdvisor API using FastAPI with Clean Architecture (Hexagonal/Ports & Adapters pattern) and Dependency Injection.

### Vision
A Python FastAPI application that analyzes board game rulebooks (photos/PDFs) using AI to:
- **User Management**: Authentication, subscriptions, credits system
- **Document Processing**: Upload and AI analysis of game rulebooks via Azure AI services
- **Knowledge Extraction**: Embedding-based content analysis and retrieval
- **AI Agent**: Real-time Q&A assistance during gameplay

### Architecture Principles
- **Clean Architecture** (Hexagonal): Domain-driven design with clear separation of concerns
- **Dependency Injection**: Loose coupling between layers
- **Azure-First**: Leveraging Azure PostgreSQL and AI services
- **Async-First**: Full async/await implementation for scalability

## Current Implementation Status ✅

### 🏗️ Foundation Complete
- ✅ **FastAPI Application**: Full server with lifespan management and CORS
- ✅ **Configuration System**: Centralized settings with Pydantic Settings + .env + JWT config
- ✅ **Database Layer**: SQLAlchemy async + Azure PostgreSQL integration
- ✅ **Migration System**: Alembic configured for schema management
- ✅ **Clean Architecture**: Complete restructuration with proper layer separation

### ✅ User Management Complete
- ✅ **Domain Entities**: User, UserSession with business logic
- ✅ **Repository Pattern**: Complete IUserRepository and IUserSessionRepository interfaces and implementations
- ✅ **Authentication Use Cases**: RegisterUser, AuthenticateUser, LogoutUser, RefreshToken
- ✅ **Session Management**: Refresh tokens, device tracking, session cleanup
- ✅ **Security Services**: JWT service, password hashing with bcrypt
- ✅ **API Endpoints**: Complete auth flow with /register, /login, /logout, /refresh
- ✅ **Comprehensive Tests**: Unit, integration, and repository tests

### 🏗️ Game Management Foundation
- ✅ **Domain Entities**: Game, GameSeries, GameImage, GameVector
- ✅ **Repository Interfaces**: Complete ports for game management
- ✅ **Use Cases**: Create, read, update, delete operations for games
- ✅ **Database Models**: SQLAlchemy models for all game entities

### 🎯 Next Phase Features
- **Document Processing**: Upload and AI analysis of game rulebooks via Azure AI services
- **Vector Search**: pgvector integration for semantic search
- **AI Agent**: Real-time Q&A assistance during gameplay
- **Game API**: REST endpoints for game management

## Architecture Structure

```
app/
├── domain/                          # Pure business logic (no dependencies)
│   ├── entities/                    # Business entities
│   │   ├── user.py                 # ✅ User entity with business methods
│   │   ├── user_session.py         # ✅ Session management entity
│   │   ├── game.py                 # ✅ Game entity
│   │   ├── game_series.py          # ✅ Game series entity
│   │   ├── game_image.py           # ✅ Game image entity
│   │   └── game_vector.py          # ✅ Game vector entity
│   ├── ports/                      # Interfaces/abstractions  
│   │   ├── repositories/           # Repository interfaces
│   │   │   ├── user_repository.py          # ✅ IUserRepository
│   │   │   ├── user_session_repository.py  # ✅ IUserSessionRepository
│   │   │   ├── game_repository.py          # ✅ IGameRepository
│   │   │   ├── game_series_repository.py   # ✅ IGameSeriesRepository
│   │   │   ├── game_image_repository.py    # ✅ IGameImageRepository
│   │   │   └── game_vector_repository.py   # ✅ IGameVectorRepository
│   │   └── services/               # Service interfaces
│   │       ├── jwt_service.py      # ✅ IJWTService
│   │       └── password_service.py # ✅ IPasswordService
│   └── use_cases/                  # Application logic orchestration
│       ├── auth/                   # ✅ Authentication use cases
│       │   ├── authenticate_user.py    # ✅ Login with session management
│       │   ├── register_user.py        # ✅ User registration
│       │   ├── logout_user.py          # ✅ Session termination
│       │   └── refresh_token.py        # ✅ Token refresh
│       └── games/                  # ✅ Game management use cases
│           ├── create_game.py          # ✅ Game creation
│           ├── get_game.py             # ✅ Game retrieval
│           ├── list_games.py           # ✅ Game listing
│           ├── update_game.py          # ✅ Game updates
│           ├── delete_game.py          # ✅ Game deletion
│           ├── create_game_series.py   # ✅ Series management
│           └── upload_game_image.py    # ✅ Image handling
├── data/                           # Data layer (was adapters/database)
│   ├── connection.py               # ✅ Database connection management
│   ├── models/                     # ✅ SQLAlchemy ORM models
│   │   ├── user.py                 # ✅ UserModel
│   │   ├── user_session.py         # ✅ UserSessionModel
│   │   ├── game.py                 # ✅ GameModel
│   │   ├── game_series.py          # ✅ GameSeriesModel
│   │   ├── game_image.py           # ✅ GameImageModel
│   │   └── game_vector.py          # ✅ GameVectorModel
│   └── repositories/               # ✅ Repository implementations
│       ├── user_repository.py          # ✅ UserRepository
│       ├── user_session_repository.py  # ✅ UserSessionRepository
│       ├── game_repository.py          # ✅ GameRepository
│       ├── game_series_repository.py   # ✅ GameSeriesRepository
│       ├── game_image_repository.py    # ✅ GameImageRepository
│       └── game_vector_repository.py   # ✅ GameVectorRepository
├── services/                       # Service implementations (was adapters/auth)
│   ├── jwt_service.py              # ✅ JWT token management
│   └── password_service.py         # ✅ Password hashing with bcrypt
├── presentation/                   # API layer (was adapters/web)
│   ├── routes/                     # FastAPI route handlers
│   │   └── auth.py                 # ✅ Authentication endpoints
│   └── schemas/                    # Pydantic request/response schemas
│       └── auth.py                 # ✅ Authentication DTOs
├── dependencies/                   # Dependency injection container
│   ├── database.py                 # ✅ Database dependencies
│   ├── repositories.py             # ✅ Repository injection
│   ├── services.py                 # ✅ Service injection
│   ├── use_cases.py                # ✅ Use case injection
│   └── auth.py                     # ✅ Authentication dependencies
├── shared/                         # Cross-cutting concerns
│   └── utils/                      # Utility functions
│       └── session_utils.py        # ✅ Session management utilities
├── config.py                       # ✅ Application configuration
└── main.py                         # ✅ FastAPI application entry point
```

## Entity Schemas

### User Management

#### User Entity
```python
@dataclass
class User:
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    hashed_password: str
    is_active: bool
    is_subscribed: bool
    credits: int
    created_at: datetime
    updated_at: datetime
    
    # Business methods:
    - create() -> User
    - activate() / deactivate()
    - subscribe() / unsubscribe()  
    - add_credits(amount) / consume_credits(amount)
    - full_name property
```

#### UserSession Entity
```python
@dataclass
class UserSession:
    id: UUID
    user_id: UUID
    refresh_token_hash: str
    device_info: Optional[Dict[str, Any]]
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime
    is_active: bool
    
    # Business methods:
    - create() -> UserSession
    - update_last_used()
    - deactivate()
    - is_expired() -> bool
    - is_valid() -> bool
```

### Game Management Entities

#### Game Entity
```python
@dataclass
class Game:
    id: UUID
    name: str
    description: Optional[str]
    min_players: int
    max_players: int
    min_age: int
    playing_time: int
    complexity: float
    series_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
```

#### GameSeries, GameImage, GameVector Entities
- ✅ Complete entity models for game series management
- ✅ Image handling with metadata
- ✅ Vector embeddings for AI search capabilities

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure database (copy and edit)
cp .env.example .env
```

### Database Operations
```bash
# Generate migration
python generate_migration.py "migration description"

# Apply migrations
python migrate.py

# Check current migration status
alembic current
alembic history
```

### Running the Application
```bash
# Development server (new path)
uvicorn app.main:app --reload

# Or via Python (new path)
python -m app.main

# Or direct execution
cd app && python main.py
```

## Configuration

### Required Environment Variables
```env
# API Configuration
API_TITLE=GameAdvisor API v2
API_VERSION=2.0.0
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Azure PostgreSQL Database
DB_HOST=your-server.postgres.database.azure.com
DB_PORT=5432
DB_NAME=gameadvisor
DB_USERNAME=your-username  
DB_PASSWORD=your-password
DB_SSL_MODE=require

# JWT Configuration (NEW)
JWT_SECRET_KEY=your-strong-256-bit-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=240
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Technology Stack

### Core Framework
- **FastAPI**: Modern async Python web framework with lifespan management
- **SQLAlchemy**: Async ORM with PostgreSQL support
- **Alembic**: Database migrations
- **Pydantic Settings**: Configuration management with validation

### Database
- **Azure PostgreSQL**: Managed database service
- **asyncpg**: Async PostgreSQL driver
- **UUID**: Primary keys for better distribution

### Authentication & Security
- **JWT**: Access and refresh token management
- **bcrypt**: Password hashing with salt
- **Session Management**: Device tracking and cleanup
- **Secure Headers**: CORS and security middleware

### Testing Framework
- **pytest**: Async testing framework
- **pytest-asyncio**: Async test support
- **httpx**: HTTP client for API testing
- **aiosqlite**: In-memory database for tests

### Future Integrations
- **Azure Computer Vision**: Image analysis
- **Azure OpenAI**: LLM integration  
- **pgvector**: Vector search capabilities (models ready)
- **Azure Blob Storage**: File storage

## Development Workflow

### 1. Domain-First Development
- Start with domain entities and business logic
- Define interfaces (ports) for external dependencies
- Keep domain layer pure (no infrastructure dependencies)

### 2. Use Case Implementation
- Implement application logic in use cases
- Orchestrate domain entities and external services
- Handle application-specific validation and workflows

### 3. Adapter Implementation  
- Implement concrete adapters for external systems
- Database repositories, external APIs, file storage
- Inject implementations via dependency injection

### 4. API Layer
- Create FastAPI routes that use use cases
- Define Pydantic schemas for request/response
- Handle HTTP concerns (status codes, validation)

## Next Development Steps

1. **Game Management API** (Foundation Ready):
   - FastAPI endpoints for game CRUD operations
   - File upload for game images
   - Game search and filtering
   - Series management endpoints

2. **Document Processing Foundation**:
   - File upload handling with validation
   - Document entity and parsing
   - Azure AI service integration
   - Vector embedding generation

3. **Vector Search Implementation**:
   - pgvector integration (models ready)
   - Semantic search endpoints
   - Content similarity matching
   - Search result ranking

4. **AI Agent Interface**:
   - Conversational chat endpoints
   - Context management with sessions
   - Integration with game knowledge base
   - Real-time assistance during gameplay

5. **Production Readiness**:
   - Error handling and logging
   - Rate limiting and security
   - Performance monitoring
   - Deployment configuration

## Testing Strategy ✅ Implemented

### Current Test Coverage
```
tests/
├── conftest.py                     # ✅ Test configuration and fixtures
├── domain/
│   ├── entities/
│   │   ├── test_user.py           # ✅ User entity business logic tests
│   │   └── test_user_session.py   # ✅ Session entity tests
│   └── use_cases/
│       └── auth/
│           ├── test_authenticate_user.py  # ✅ Login flow tests
│           ├── test_register_user.py      # ✅ Registration tests
│           ├── test_logout_user.py        # ✅ Logout tests
│           └── test_refresh_token.py      # ✅ Token refresh tests
├── data/repositories/
│   ├── test_user_repository.py        # ✅ User repository tests
│   └── test_user_session_repository.py # ✅ Session repository tests
├── services/
│   ├── test_jwt_service.py            # ✅ JWT service tests
│   └── test_password_service.py       # ✅ Password service tests
└── integration/
    └── test_auth_flow.py              # ✅ End-to-end auth flow tests
```

### Test Types
- **Unit Tests**: Domain entities, use cases, and services
- **Repository Tests**: Database operations with in-memory SQLite
- **Integration Tests**: Full authentication flow testing
- **Service Tests**: JWT and password hashing functionality

## Code Style Guidelines

### Documentation et Commentaires
- **Langue**: Tous les docstrings et commentaires doivent être rédigés en français
- **Docstrings**: Obligatoires pour toutes les classes, méthodes et fonctions publiques
- **Commentaires**: Explications en français pour la logique métier complexe
- **Pas d'emojis**: Aucun emoji dans le code, commentaires ou docstrings

### Collaboration avec Claude
- **Pas d'écriture directe**: Claude ne doit jamais écrire de code directement dans les fichiers
- **Fourniture de code**: Claude fournit le code à insérer, l'utilisateur l'insère manuellement
- **Review avant insertion**: Validation du code proposé avant intégration