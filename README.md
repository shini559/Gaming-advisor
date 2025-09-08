# 🎲 Gaming Advisor

**Gaming Advisor** est une plateforme IA conversationnelle spécialisée dans l'assistance aux jeux de société. Elle utilise des techniques avancées de traitement d'images et de recherche vectorielle (RAG) pour fournir une aide contextuelle intelligente aux joueurs.

## 🎯 Objectif du Projet

Gaming Advisor vise à révolutionner l'expérience des jeux de société en proposant :
- **Simplification des règles complexes** : Fini les manuels de 50 pages, posez vos questions directement à l'IA
- **Setup rapide** : Envoyez une photo de votre boîte de jeu et recevez des instructions pas à pas
- **Conseils personnalisés** : Obtenez des stratégies et astuces adaptées à votre situation de jeu
- **Assistant multimodal** : Compréhension des images et du texte pour un support complet

## 🏗️ Architecture du Projet

Le projet suit une **architecture Clean/Hexagonale** avec séparation claire des responsabilités :

```
Gaming-advisor/
├── 📁 prototype/          # Prototype initial Streamlit + LangChain
├── 📁 API/                # API (Clean Architecture)
│   ├── 📁 app/
│   │   ├── 📁 domain/     # Entités métier et ports
│   │   ├── 📁 data/       # Modèles SQL et repositories
│   │   ├── 📁 services/   # Services externes (OpenAI, Azure, Redis)
│   │   ├── 📁 presentation/ # Routes API et schémas
│   │   └── 📁 dependencies/ # Injection de dépendances
│   └── 📁 migrations/     # Migrations Alembic
└── 📁 front-end/          # Interface utilisateur Next.js
```

## 🚀 Technologies Utilisées

### Backend (API)
- **Framework** : FastAPI 0.115+ (Python asyncio)
- **Architecture** : Domain Driven Design (DDD) + Clean Architecture
- **Base de données** : PostgreSQL avec extension pgvector
- **ORM** : SQLAlchemy 2.0 (mode asyncio)
- **Migrations** : Alembic
- **Authentication** : JWT avec python-jose + bcrypt
- **Storage** : Azure Blob Storage
- **Queue** : Redis + Background workers
- **IA** : OpenAI GPT-4 Vision + Embeddings text-embedding-3-small
- **Tests** : pytest + pytest-asyncio

### Frontend
- **Framework** : Next.js 15 (React 19)
- **Language** : TypeScript
- **Styling** : Tailwind CSS 4.0
- **Icons** : Heroicons
- **Build** : Turbopack

### Prototype (Legacy)
- **Interface** : Streamlit
- **RAG** : LangChain + ChromaDB
- **Multimodal** : Support OpenAI, DeepSeek, Ollama

## 🎮 Fonctionnalités Principales

### 1. 🔐 Authentification et Gestion Utilisateurs
- **Inscription/Connexion** avec validation email
- **Profils utilisateurs** complets (avatar, crédits tokens)
- **Sessions sécurisées** JWT avec refresh tokens
- **Niveaux d'autorisation** (admin/utilisateur)

### 2. 🎲 Gestion des Jeux
- **Catalogue de jeux** avec métadonnées complètes
- **Organisation en séries** (jeu de base + extensions)
- **Jeux publics/privés** avec contrôle d'accès
- **Avatars personnalisés** stockés sur Azure

### 3. 📸 Traitement d'Images Intelligentes
- **Upload par batch** avec traitement asynchrone
- **OCR avancé** pour extraction du texte des règles
- **Description automatique** des composants de jeu
- **Labeling intelligent** des éléments visuels
- **Vectorisation** avec OpenAI text-embedding-3-small
- **Retry automatique** en cas d'échec
- **Monitoring** temps réel des batches

### 4. 🤖 Agent Conversationnel IA avec RAG
- **Chat contextuel** basé sur les règles de jeux spécifiques
- **Recherche vectorielle** dans les contenus textuels et visuels
- **Réponses sourcées** avec références précises
- **Historique des conversations** persistant
- **Système de feedback** pour amélioration continue
- **Refus intelligent** des questions hors-domaine

### 5. 🔄 Architecture Évolutive
- **Clean Architecture** avec séparation des couches
- **Tests automatisés** (unitaires + intégration + sécurité)
- **Containerisation Docker** prête pour production
- **CI/CD** compatible Azure Container Apps
- **Monitoring** et logging détaillés

## 🚦 Installation et Démarrage

### Prérequis
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ avec extension pgvector
- Redis 7+
- Compte OpenAI API
- Compte Azure (Blob Storage)

### 🐳 Démarrage Rapide avec Docker

```bash
# Cloner le repository
git clone &lt;repository-url&gt;
cd Gaming-advisor

# Configurer les variables d'environnement
cp API.env.example API.env
# Éditer APIv2/.env avec vos clés API

# Lancer l'API avec Docker
cd API
docker-compose up -d

# L'API sera disponible sur http://localhost:8000
```

### 🔧 Installation Développement

#### Backend
```bash
cd API

# Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Installer dépendances
pip install -r requirements.txt

# Configurer base de données
alembic upgrade head

# Lancer serveur de développement
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd front-end/gaming-advisor

# Installer dépendances
npm install

# Lancer serveur de développement
npm run dev

# L'interface sera disponible sur http://localhost:3000
```

#### Prototype Legacy
```bash
cd prototype

# Créer environnement virtuel
python -m venv .venv
source .venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Lancer prototype
streamlit run main.py
```

## 📋 Variables d'Environnement

### API/.env
```env
# API Configuration
API_TITLE=GameAdvisor API v2
API_VERSION=2.0.0
DEBUG=true

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database Configuration (Azure PostgreSQL)
DB_HOST=your-azure-postgres-server.postgres.database.azure.com
DB_PORT=5432
DB_NAME=gameadvisor
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_SSL_MODE=require

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-256-bits-minimum
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=240
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING="YourConnectionString"
AZURE_STORAGE_ACCOUNT=ACCOUNT
AZURE_STORAGE_KEY=KEY
AZURE_BLOB_CONTAINER_NAME=NAME

# Redis
REDIS_URL=URL

REDIS_HOST=HOST
REDIS_PORT=6380
REDIS_PASSWORD=PASSWORD
REDIS_SSL=true

# OpenAI
AZURE_OPENAI_API_KEY=KEY
AZURE_OPENAI_ENDPOINT=ENDPOINT
AZURE_OPENAI_VISION_DEPLOYMENT=MODEL
AZURE_OPENAI_VISION_API_VERSION=MODEL
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=MODEL
AZURE_OPENAI_EMBEDDING_API_VERSION=VERSION
```

## 🧪 Tests

```bash
cd API

# Tests unitaires
pytest tests/domain/

# Tests d'intégration  
pytest tests/integration/

# Tests de sécurité
pytest tests/integration/test_*_security.py

# Coverage
pytest --cov=app tests/
```

## 📖 Documentation API

Une fois l'API lancée :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Endpoints Principaux

#### Authentification
- `POST /auth/register` - Inscription utilisateur
- `POST /auth/login` - Connexion
- `GET /auth/me` - Profil utilisateur
- `POST /auth/refresh` - Renouvellement token

#### Jeux
- `GET /games` - Liste des jeux accessibles
- `POST /games` - Créer un jeu
- `GET /games/{game_id}` - Détails d'un jeu
- `PUT /games/{game_id}` - Modifier un jeu

#### Images
- `POST /images/games/{game_id}/upload` - Upload batch d'images
- `GET /images/batches/{batch_id}/status` - Statut traitement

#### Chat IA
- `POST /chat/conversations` - Créer conversation
- `POST /chat/messages` - Envoyer message
- `GET /chat/conversations/{conv_id}/history` - Historique
- `POST /chat/messages/{msg_id}/feedback` - Feedback

## 🔍 Architecture Technique Détaillée

### Traitement d'Images
1. **Upload** : Réception fichiers via FastAPI multipart
2. **Validation** : Vérification format, taille, type MIME
3. **Storage** : Sauvegarde Azure Blob Storage
4. **Queue** : Ajout tâche Redis pour traitement async
5. **Processing** : 
   - OCR avec Azure Vision API
   - Description avec GPT-4 Vision
   - Labeling automatique
   - Vectorisation avec text-embedding-3-small
6. **Indexation** : Stockage vecteurs PostgreSQL (pgvector)

### Pipeline RAG
1. **Question utilisateur** → Vectorisation query
2. **Recherche similarité** → Top-k résultats filtrés par game_id
3. **Context assembly** → Agrégation texte + images pertinentes  
4. **Prompt engineering** → Template spécialisé jeux de société
5. **Génération** → GPT-4 Vision avec context multimodal
6. **Post-processing** → Extraction sources + formatage réponse

### Sécurité
- **Authentication** : JWT avec refresh tokens
- **Authorization** : RBAC sur ressources par utilisateur
- **Input validation** : Pydantic schemas stricts
- **Rate limiting** : Protection contre abus API
- **CORS** : Configuration sécurisée pour production
- **SQL Injection** : Protection via SQLAlchemy ORM
- **File upload** : Validation stricte types et tailles

## 🚀 Déploiement Production

Le projet est conçu pour Azure Container Apps :

```bash
# Build image production
docker build -t gameadvisor-api:latest .

# Push vers registry
docker push your-registry/gameadvisor-api:latest

# Deploy via Azure CLI
az containerapp update --name gameadvisor-api --resource-group rg-gameadvisor --image your-registry/gameadvisor-api:latest
```

## 📄 Licence

Ce projet est sous licence [MIT](LICENSE).

---

**Gaming Advisor** - *Votre copilote IA pour les jeux de société* 🤖🎲