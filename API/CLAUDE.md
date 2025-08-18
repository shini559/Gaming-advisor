# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GameAdvisor API - Une API Python qui analyse les livrets de règles de jeux (photos/PDF) via IA pour :
- Scanner et extraire le texte/images des livrets de règles
- Analyser le contenu avec des modèles de vision et NLP
- Réexpliquer les règles de manière claire
- Donner des conseils de mise en place
- Fournir une assistance en temps réel pendant les parties avec TTS

## Environment Setup

This project uses a Python virtual environment located in `venv/`. 

### Activation Commands
- **Windows (Git Bash/MinGW64)**: `source venv/Scripts/activate`
- **Windows (Command Prompt)**: `venv\Scripts\activate.bat`
- **Windows (PowerShell)**: `venv\Scripts\Activate.ps1`

## Development Workflow

Since this is a new project, the following commands should be established as the codebase develops:

### Common Commands
- Install dependencies: `pip install -r requirements.txt`
- Run the API server: `uvicorn main:app --reload` (FastAPI recommended)
- Run tests: `python -m pytest tests/`
- Format code: `black . && isort .`
- Lint code: `ruff check .`
- Type check: `mypy .`

## Architecture Notes

### Core Components
1. **Document Processing Service** (`services/document_processor.py`)
   - OCR pour extraction de texte (Tesseract/AWS Textract)
   - Traitement d'images (OpenCV/Pillow)
   - Conversion PDF vers images

2. **AI Analysis Service** (`services/ai_analyzer.py`)
   - Intégration modèles de vision (GPT-4V, Claude 3.5 Sonnet)
   - Analyse sémantique des règles
   - Extraction d'informations structurées

3. **Rules Engine** (`services/rules_engine.py`)
   - Stockage structuré des règles analysées
   - Recherche contextuelle
   - Système de questions/réponses

4. **TTS Service** (`services/tts_service.py`)
   - Synthèse vocale (Azure Speech/Google TTS/ElevenLabs)
   - Gestion audio en streaming
   - Support multilingue

5. **Game Session Manager** (`services/session_manager.py`)
   - Suivi des parties en cours
   - Contexte des questions
   - Historique des interactions

### Technology Stack
- **API Framework**: FastAPI (async support, auto-documentation)
- **Database**: PostgreSQL + Vector DB (pgvector pour recherche sémantique)
- **File Storage**: AWS S3 ou local storage
- **Cache**: Redis pour sessions et réponses fréquentes
- **AI Models**: OpenAI GPT-4V, Anthropic Claude 3.5 Sonnet
- **OCR**: Tesseract OCR + preprocessing

### Project Structure
```
/
├── app/
│   ├── api/          # Endpoints FastAPI
│   ├── models/       # Modèles Pydantic/SQLAlchemy
│   ├── services/     # Logique métier
│   ├── utils/        # Utilitaires
│   └── config.py     # Configuration
├── tests/            # Tests unitaires/intégration
├── uploads/          # Stockage temporaire fichiers
└── requirements.txt  # Dépendances Python
```

## Development Guidelines

### API Design
- Endpoints RESTful avec préfixe `/api/v1/`
- Upload: `POST /api/v1/games/upload` (PDF/images)
- Analysis: `GET /api/v1/games/{game_id}/rules`
- Questions: `POST /api/v1/games/{game_id}/ask`
- TTS: `POST /api/v1/games/{game_id}/speak`

### Data Flow
1. Upload → Document Processing → AI Analysis → Rules Storage
2. Runtime: Question → Context Search → AI Response → TTS

### Key Dependencies à installer
- `fastapi uvicorn` - API framework
- `opencv-python pillow` - Traitement d'images
- `pytesseract` - OCR
- `openai anthropic` - Modèles IA
- `sqlalchemy alembic` - Base de données
- `redis` - Cache
- `pydantic` - Validation données
- `python-multipart` - Upload fichiers

### Patterns Importants
- Async/await pour I/O (API calls, DB, file processing)
- Type hints obligatoires (mypy strict)
- Dependency injection FastAPI pour services
- Error handling avec codes HTTP appropriés
- Logging structuré (JSON) pour monitoring