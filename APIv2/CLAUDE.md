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
- ✅ **FastAPI Application**: Basic server with configuration management
- ✅ **Configuration System**: Centralized settings with Pydantic Settings + .env
- ✅ **Database Layer**: SQLAlchemy async + Azure PostgreSQL integration
- ✅ **Migration System**: Alembic configured for schema management
- ✅ **User Model**: Complete user entity with domain logic

### 🔄 In Progress
- **User Management**: Registration/authentication use cases
- **Repository Pattern**: IUserRepository interface and implementation
- **API Endpoints**: User registration, login, profile management

### 🎯 Planned Features
- Document upload and processing
- Azure AI integration (Computer Vision, OpenAI)
- Vector embeddings and search
- AI agent conversational interface

## Architecture Structure

```
app/
├── domain/                          # Pure business logic (no dependencies)
│   ├── entities/                    # Business entities
│   │   └── user.py                 # ✅ User entity with business methods
│   ├── ports/                      # Interfaces/abstractions  
│   │   ├── repositories/           # Repository interfaces (IUserRepository)
│   │   └── services/               # Service interfaces (IAuthService)
│   └── exceptions/                 # Domain-specific exceptions
├── use_cases/                      # Application logic orchestration
│   ├── auth/                      # RegisterUser, AuthenticateUser, etc.
│   ├── games/                     # (future: game management)
│   └── documents/                 # (future: document processing)
├── adapters/                      # Infrastructure implementations
│   ├── database/                  # ✅ Database layer
│   │   ├── models/                # ✅ SQLAlchemy models (UserModel)
│   │   ├── repositories/          # Repository implementations
│   │   └── connection.py          # ✅ Database connection management
│   ├── auth/                      # JWT, password hashing
│   ├── external/                  # Azure AI services, etc.
│   └── web/                       # FastAPI routes, schemas, dependencies
│       ├── routes/
│       ├── schemas/
│       └── dependencies/
└── shared/                        # Cross-cutting concerns
    ├── config/                    # Configuration management
    ├── exceptions/                # Base exceptions
    └── utils/                     # Utilities
```

## User Entity Schema

### Database Model (SQLAlchemy)
```python
class UserModel(Base):
    id: UUID (Primary Key)
    username: str (Unique, 50 chars)
    email: str (Unique, 255 chars) 
    first_name: str (100 chars)
    last_name: str (100 chars)
    hashed_password: str (255 chars)
    is_active: bool (default: True)
    is_subscribed: bool (default: False) 
    credits: int (default: 0)
    created_at: datetime
    updated_at: datetime
```

### Domain Entity
```python
@dataclass
class User:
    # Business methods:
    - create() -> User
    - activate() / deactivate()
    - subscribe() / unsubscribe()  
    - add_credits(amount) / consume_credits(amount)
    - full_name property
```

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
# Development server
uvicorn main:app --reload

# Or via Python
python main.py
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
```

## Technology Stack

### Core Framework
- **FastAPI**: Modern async Python web framework
- **SQLAlchemy**: Async ORM with PostgreSQL support
- **Alembic**: Database migrations
- **Pydantic Settings**: Configuration management

### Database
- **Azure PostgreSQL**: Managed database service
- **asyncpg**: Async PostgreSQL driver
- **UUID**: Primary keys for better distribution

### Future Integrations
- **Azure Computer Vision**: Image analysis
- **Azure OpenAI**: LLM integration  
- **pgvector**: Vector search capabilities
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

1. **Complete User Management**:
   - IUserRepository interface and implementation
   - RegisterUser and AuthenticateUser use cases  
   - Password hashing and JWT services
   - User registration/login API endpoints

2. **Document Processing Foundation**:
   - File upload handling
   - Azure AI service integration
   - Document entity and use cases

3. **Knowledge Management**:
   - Vector embeddings integration
   - Search and retrieval capabilities

4. **AI Agent Interface**:
   - Conversational endpoints
   - Context management
   - Integration with knowledge base

## Testing Strategy
- **Unit Tests**: Domain entities and use cases
- **Integration Tests**: Database operations, external services  
- **API Tests**: FastAPI endpoint testing
- **Migration Tests**: Database schema validation

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