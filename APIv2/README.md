# GameAdvisor API v2

Une API FastAPI complète et sophistiquée qui utilise l'Intelligence Artificielle pour analyser les livres de règles de jeux de société et fournir une assistance en temps réel aux joueurs.

## 🎯 Vision du Projet

GameAdvisor API v2 est une refonte complète utilisant les principes d'architecture propre (Clean Architecture) pour créer un assistant IA spécialisé dans les jeux de société. L'application analyse automatiquement les livrets de règles (photos/PDFs) via les services Azure AI et fournit une assistance conversationnelle intelligente pendant le jeu.

### Fonctionnalités Principales

- **🔐 Gestion d'Utilisateurs** : Authentification JWT complète avec gestion des sessions et système de crédits
- **📄 Traitement de Documents** : Upload et analyse IA des livrets de règles via Azure AI Vision
- **🧠 Extraction de Connaissance** : Analyse de contenu basée sur des embeddings et recherche sémantique
- **🤖 Agent IA Conversationnel** : Assistance Q&A en temps réel utilisant RAG (Retrieval Augmented Generation)
- **🎮 Gestion de Jeux** : CRUD complet pour les jeux avec support des images et métadonnées

## 🏗️ Architecture

### Paradigme Architectural

Le projet implémente l'**Architecture Propre (Hexagonale)** avec les couches suivantes :

```
📁 app/
├── domain/           # 🎯 Logique métier pure (aucune dépendance externe)
│   ├── entities/     # Entités métier avec méthodes business
│   ├── ports/        # Interfaces (repositories, services)
│   └── use_cases/    # Logique d'application et orchestration
├── data/            # 💾 Couche de données (anciennement adapters/database)
│   ├── models/      # Modèles SQLAlchemy ORM
│   └── repositories/ # Implémentations concrètes des repositories
├── services/        # 🔧 Implémentations de services (anciennement adapters/auth)
├── presentation/    # 🌐 Couche API (anciennement adapters/web)
│   ├── routes/      # Endpoints FastAPI
│   └── schemas/     # Schémas Pydantic request/response
├── dependencies/    # 🔗 Container d'injection de dépendance
└── shared/         # 🛠️ Concerns transversaux
```

### Principes Clés

- **🎯 Domain-Driven Design** : Logique métier au centre, indépendante des détails techniques
- **🔌 Injection de Dépendances** : Couplage faible entre les couches
- **☁️ Azure-First** : Exploitation intensive des services Azure (PostgreSQL, AI, Blob Storage)
- **⚡ Async-First** : Implémentation async/await complète pour la scalabilité

## 📊 Entités Principales

### 👤 Gestion d'Utilisateurs

```python
@dataclass
class User:
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    token_credits: int = 0
    # Méthodes métier : activate(), deactivate(), full_name
```

```python
@dataclass  
class UserSession:
    id: UUID
    user_id: UUID
    refresh_token_hash: str
    device_info: Optional[Dict]
    expires_at: datetime
    # Méthodes métier : is_expired(), is_valid(), update_last_used()
```

### 🎮 Système de Jeux

```python
@dataclass
class Game:
    id: UUID
    title: str
    publisher: Optional[str]
    description: Optional[str]
    series_id: Optional[UUID]
    is_expansion: bool
    base_game_id: Optional[UUID]
    is_public: bool
    created_by: UUID
    avatar: Optional[str]  # URL Azure Blob Storage
```

### 🖼️ Traitement d'Images Avancé

```python
class ImageProcessingStatus(Enum):
    UPLOADED = "uploaded"      # Fichier uploadé, en attente
    PROCESSING = "processing"  # En cours de traitement IA
    COMPLETED = "completed"    # Traitement terminé avec succès
    FAILED = "failed"         # Échec du traitement
    RETRYING = "retrying"     # Nouvel essai en cours
```

```python
@dataclass
class ImageBatch:
    id: UUID
    game_id: UUID
    total_images: int
    processed_images: int = 0
    failed_images: int = 0
    status: BatchStatus
    retry_count: int = 0
    max_retries: int
    
    # Propriétés calculées
    @property
    def progress_ratio(self) -> str:     # "15/30"
        return f"{self.processed_images}/{self.total_images}"
    
    @property 
    def completion_percentage(self) -> float:  # 50.0
        return (self.processed_images / self.total_images) * 100
```

### 🔍 Vectorisation et Recherche Sémantique

```python
@dataclass
class GameVector:
    id: UUID
    game_id: UUID
    image_id: UUID
    
    # Architecture 3-paires pour flexibilité maximale
    ocr_content: Optional[str] = None              # Texte extrait par OCR
    ocr_embedding: Optional[List[float]] = None    # Embedding du texte OCR
    
    description_content: Optional[str] = None       # Description visuelle IA
    description_embedding: Optional[List[float]] = None
    
    labels_content: Optional[str] = None           # Métadonnées JSON structurées
    labels_embedding: Optional[List[float]] = None
    
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None       # Calculé pendant la recherche
```

### 💬 Système de Chat Conversationnel

```python
@dataclass
class ChatConversation:
    id: UUID
    game_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    
    def touch(self) -> None:  # Met à jour le timestamp lors de nouveaux messages
```

```python
@dataclass
class ChatMessage:
    id: UUID
    conversation_id: UUID
    role: MessageRole        # USER, ASSISTANT
    content: str
    sources: List[MessageSource] = None  # Sources utilisées par l'IA
    search_method: Optional[str] = None  # Configuration RAG utilisée
```

## 🧠 Pipeline de Traitement IA

### 1. Upload et Stockage
- Upload vers **Azure Blob Storage** dans des dossiers organisés : `games/{game_id}/batch_{batch_id}/`
- Validation des formats, tailles et permissions de sécurité
- Création d'entités `GameImage` en base de données

### 2. Traitement par Batch en Parallèle
- **Queue Redis** : Jobs de traitement avec retry automatique
- **Worker Background** : Traitement parallèle configuré (défaut : 5 workers)
- **Suivi en Temps Réel** : Statuts détaillés avec ratios de progression

### 3. Analyse IA Multi-Modale (Azure OpenAI)

```python
# Configuration découplée et flexible
enable_ocr: bool = True                 # OCR extraction
enable_visual_description: bool = True  # Description visuelle
enable_labeling: bool = True           # Métadonnées JSON

# Prompts IA spécialisés
ocr_prompt: str = """Extracte tout le texte visible dans cette image de règles..."""

vision_description_prompt: str = """Analyse cette page de règles:
1. TEXTE: Extrait tout le texte visible  
2. SCHÉMAS: Décris précisément tous diagrammes, tableaux
3. ÉLÉMENTS: Identifie les composants (cartes, pions, dés...)
4. RÈGLES: Extrait les règles et mécaniques spécifiques
5. SECTIONS: Catégorise (setup, gameplay, scoring, endgame)"""

vision_labeling_prompt: str = """Extrait des métadonnées structurées en JSON:
- game_elements, diagrams, game_actions, key_concepts, sections"""
```

### 4. Génération d'Embeddings
- **Modèle** : Azure OpenAI `text-embedding-3-small` (1536 dimensions)
- **Triple vectorisation** : OCR, Description visuelle, Labels JSON
- **Stockage** : PostgreSQL avec extension **pgvector**

### 5. Recherche Vectorielle Sémantique

```python
# Configuration de recherche découplée
vector_search_method: str = "description"    # "ocr" | "description" | "labels"
vector_search_top_k: int = 5                # Nombre de résultats
vector_similarity_threshold: float = 0.1    # Seuil de similarité

# Configuration de l'agent IA
agent_send_images: bool = True                    # Envoyer images à l'agent
agent_content_fields: List[str] = ["ocr"]        # Champs texte pour l'agent
agent_max_context_length: int = 8000             # Limite de contexte
```

## 🤖 Agent IA Conversationnel (RAG)

### Architecture RAG Avancée

L'agent IA utilise une approche **RAG (Retrieval Augmented Generation)** sophistiquée :

1. **Recherche Sémantique** : Trouve les passages pertinents via embeddings
2. **Contexte Multi-Modal** : Combine texte extrait + images originales
3. **Génération Contextuelle** : GPT-4 Vision génère des réponses basées sur le contexte
4. **Traçabilité** : Sources et scores de confiance pour chaque réponse

### Configuration Découplée

```python
# Stratégie de recherche : quel embedding utiliser pour la similarité
vector_search_method: str = "description"  # "ocr" | "description" | "labels"

# Contenu envoyé à l'agent : multi-sélection possible  
agent_content_fields: List[str] = ["ocr", "description"]  # ["ocr", "description", "labels"]

# Images : envoi des images originales en plus du texte
agent_send_images: bool = True
```

### Prompt Système Spécialisé

```python
agent_system_prompt = '''You are a game master & boardgame assistant. 
Your role is to assist board gamers in setting up games, understanding rules, calculating scores.

ONLY USE THE DATA THEY PROVIDE TO ANSWER THEIR QUESTIONS! 
YOU MUST NEVER ANSWER A QUESTION ABOUT GAME RULES IF YOU HAVE NOT BEEN PROVIDED DATA!

Answer questions clearly and directly. Use simple French.'''
```

## 🌐 API REST Complète

### 🔐 Authentification JWT

```http
POST /auth/register     # Création de compte
POST /auth/login        # Connexion avec gestion de session  
POST /auth/refresh      # Renouvellement de token
POST /auth/logout       # Déconnexion
GET  /auth/me          # Profil utilisateur
```

### 🎮 Gestion de Jeux

```http
POST /games/create              # Création avec avatar optionnel
GET  /games                     # Jeux accessibles (publics + privés utilisateur)
GET  /games/my                  # Jeux créés par l'utilisateur
PUT  /games/{game_id}/update    # Mise à jour avec avatar
```

### 🖼️ Upload et Traitement d'Images

```http
# Upload en lot avec traitement parallèle
POST /images/games/{game_id}/batch-upload
Response: {
  "batch_id": "uuid",
  "total_images": 25,
  "uploaded_images": 25,
  "status": "pending",
  "message": "Batch créé avec succès - 25 images uploadées"
}

# Suivi détaillé du traitement
GET /images/batches/{batch_id}/status  
Response: {
  "batch_id": "uuid",
  "status": "processing", 
  "total_images": 30,
  "processed_images": 15,
  "failed_images": 2,
  "progress_ratio": "15/30",
  "completion_percentage": 50.0,
  "failure_percentage": 6.67,
  "can_retry": true
}
```

### 💬 Chat Conversationnel

```http
POST /chat/conversations                            # Créer une conversation
POST /chat/messages                                 # Envoyer un message à l'IA  
GET  /chat/conversations/{id}/history              # Historique de conversation
POST /chat/messages/{message_id}/feedback          # Feedback sur réponse IA
GET  /chat/games/{game_id}/conversations           # Conversations pour un jeu
```

## 🛠️ Stack Technique

### Framework Core
- **FastAPI** : Framework web async moderne avec gestion de cycle de vie
- **SQLAlchemy 2.0** : ORM async avec support PostgreSQL complet
- **Alembic** : Migrations de base de données
- **Pydantic Settings** : Configuration avec validation

### Base de Données et Stockage  
- **Azure PostgreSQL** : Base de données managée
- **pgvector** : Extension PostgreSQL pour recherche vectorielle
- **Azure Blob Storage** : Stockage de fichiers organisé
- **asyncpg** : Driver PostgreSQL async

### Intelligence Artificielle
- **Azure OpenAI** : GPT-4 Vision pour analyse multimodale
- **Azure OpenAI Embeddings** : text-embedding-3-small pour vectorisation
- **Pillow** : Traitement et optimisation d'images

### Queue et Background Processing
- **Redis** : Queue de jobs avec retry et suivi de statut
- **Worker Custom** : Traitement async parallèle avec support de batch
- **Retry Logic** : Mécanismes de retry configurables

### Authentification et Sécurité
- **JWT** : Gestion des tokens d'accès et de refresh
- **bcrypt** : Hachage sécurisé des mots de passe  
- **Session Management** : Suivi des appareils et nettoyage automatique
- **CORS** : Middleware de sécurité

### Tests et Qualité
- **pytest** : Framework de test async
- **httpx** : Client HTTP pour tests d'intégration
- **aiosqlite** : Base en mémoire pour tests
- **Type Hints** : Typage complet avec validation

## ⚙️ Configuration

### Variables d'Environnement Critiques

```env
# API Configuration
API_TITLE=GameAdvisor API v2
API_VERSION=2.0.0
DEBUG=true

# Azure PostgreSQL
DB_HOST=your-server.postgres.database.azure.com  
DB_NAME=gameadvisor
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_SSL_MODE=require

# JWT Security
JWT_SECRET_KEY=your-strong-256-bit-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=240
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Azure Blob Storage  
AZURE_STORAGE_ACCOUNT=your-storage-account
AZURE_STORAGE_KEY=your-storage-key
AZURE_BLOB_CONTAINER_NAME=gameadvisorstorage

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://gameadvisorai.openai.azure.com/
AZURE_OPENAI_VISION_DEPLOYMENT=hybrid_vision-gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536

# Redis & Queue
REDIS_URL=redis://localhost:6379/0
BATCH_MAX_RETRIES=3
BATCH_PARALLEL_WORKERS=5

# IA Processing Configuration (découplée)
vector_search_method=description          # "ocr" | "description" | "labels" 
agent_send_images=true                     # Envoyer images à l'agent
agent_content_fields=["ocr", "description"] # Champs texte pour l'agent
vector_search_top_k=5                     # Nombre de résultats similaires
vector_similarity_threshold=0.1           # Seuil de similarité
```

## 🚀 Commandes de Développement

### Installation
```bash
# Dépendances
pip install -r requirements.txt

# Configuration (.env à partir de .env.example)
cp .env.example .env
```

### Base de Données
```bash
# Créer une migration
python generate_migration.py "description de la migration"

# Appliquer les migrations  
python migrate.py

# Statut des migrations
alembic current
alembic history
```

### Lancement
```bash
# Serveur de développement
uvicorn app.main:app --reload

# Ou via Python
python -m app.main

# Ou exécution directe
cd app && python main.py
```

## 📈 État Actuel du Développement

### ✅ Fonctionnalités Complètement Implémentées

#### 🏗️ Fondation Solide
- ✅ **Application FastAPI** : Serveur complet avec gestion de cycle de vie et CORS
- ✅ **Système de Configuration** : Settings centralisées avec Pydantic + .env + JWT
- ✅ **Couche Base de Données** : SQLAlchemy async + intégration Azure PostgreSQL  
- ✅ **Système de Migration** : Alembic configuré pour la gestion de schéma
- ✅ **Architecture Propre** : Restructuration complète avec séparation des couches

#### 👤 Gestion d'Utilisateurs Complète
- ✅ **Entités Domaine** : User, UserSession avec logique métier
- ✅ **Pattern Repository** : Interfaces et implémentations complètes
- ✅ **Use Cases d'Auth** : RegisterUser, AuthenticateUser, LogoutUser, RefreshToken
- ✅ **Gestion de Sessions** : Tokens de refresh, suivi d'appareils, nettoyage
- ✅ **Services de Sécurité** : Service JWT, hachage de mots de passe avec bcrypt
- ✅ **Endpoints API** : Flow d'auth complet avec /register, /login, /logout, /refresh
- ✅ **Tests Complets** : Tests unitaires, d'intégration et de repository

#### 🎮 Gestion de Jeux et Traitement d'Images
- ✅ **Entités Domaine** : Game, GameSeries, GameImage, GameVector, ImageBatch
- ✅ **Interfaces Repository** : Ports complets pour la gestion de jeux et images
- ✅ **Use Cases** : Opérations CRUD complètes pour les jeux
- ✅ **Modèles Base de Données** : Modèles SQLAlchemy pour toutes les entités
- ✅ **API Jeux** : Endpoints REST pour opérations CRUD des jeux

#### 📸 Système de Traitement d'Images Complet
- ✅ **Upload Image Unique** : Upload individuel avec traitement IA
- ✅ **Upload en Batch** : Upload multiple avec traitement parallèle  
- ✅ **Intégration Azure OpenAI** : GPT-4 Vision + Embeddings pour OCR, description, labelling
- ✅ **Stockage Vectoriel** : Génération automatique d'embeddings et stockage pgvector
- ✅ **Système de Queue** : Queue Redis avec mécanismes de retry et support batch
- ✅ **Suivi de Statut** : Monitoring en temps réel avec ratios détaillés
- ✅ **Worker Background** : Worker async de traitement avec parallélisation des batchs
- ✅ **Blob Storage** : Intégration Azure Blob Storage avec structure de dossiers organisée

#### 💬 Système de Chat IA Conversationnel
- ✅ **Agent IA RAG** : Agent conversationnel utilisant Retrieval Augmented Generation
- ✅ **Recherche Vectorielle** : Recherche sémantique dans les règles via embeddings
- ✅ **Context Multi-Modal** : Combine texte extrait + images originales
- ✅ **Configuration Découplée** : Paramétrage flexible des méthodes de recherche et contenu
- ✅ **Gestion de Conversations** : CRUD complet pour conversations et messages
- ✅ **Historique et Sources** : Traçabilité complète des réponses avec sources
- ✅ **API Chat Complète** : Endpoints pour créer conversations, envoyer messages, feedback

### 🎯 Prochaines Évolutions Possibles

1. **🔍 Recherche Vectorielle Étendue** : 
   - Endpoints de recherche sémantique publics
   - Recherche par similarité d'images
   - Recommandations de jeux basées sur les règles

2. **📊 Analytics et Monitoring** :
   - Métriques d'utilisation de l'IA
   - Dashboard d'administration
   - Logs structurés et monitoring

3. **🎮 Fonctionnalités Avancées** :
   - Mode "partie en cours" avec contexte persistant
   - Calculs automatiques de score
   - Intégration de timers de jeu

4. **🔧 Production Ready** :
   - Rate limiting et throttling
   - Cache intelligent des réponses IA  
   - Déploiement containerisé avec Docker/Kubernetes
   - Pipeline CI/CD complet

## 🧪 Stratégie de Test

### 📊 Couverture de Test Actuelle

```
tests/
├── conftest.py                     # ✅ Configuration et fixtures de test
├── domain/
│   ├── entities/
│   │   ├── test_user.py           # ✅ Tests logique métier User
│   │   └── test_user_session.py   # ✅ Tests entité Session  
│   └── use_cases/
│       └── auth/
│           ├── test_authenticate_user.py  # ✅ Tests flow de login
│           ├── test_register_user.py      # ✅ Tests d'inscription
│           ├── test_logout_user.py        # ✅ Tests de logout
│           └── test_refresh_token.py      # ✅ Tests refresh token
├── data/repositories/
│   ├── test_user_repository.py        # ✅ Tests repository utilisateur
│   └── test_user_session_repository.py # ✅ Tests repository session
├── services/
│   ├── test_jwt_service.py            # ✅ Tests service JWT
│   └── test_password_service.py       # ✅ Tests service mot de passe
└── integration/
    └── test_auth_flow.py              # ✅ Tests end-to-end auth complet
```

### Types de Tests
- **Tests Unitaires** : Entités domaine, use cases, services
- **Tests Repository** : Opérations base de données avec SQLite en mémoire
- **Tests d'Intégration** : Flow d'authentification complet
- **Tests Services** : Fonctionnalités JWT et hachage de mots de passe

## 🎖️ Points d'Excellence du Projet

### 🏆 Architecture et Design
- **Architecture Hexagonale Exemplaire** : Séparation parfaite des préoccupations
- **Domain-Driven Design** : Logique métier pure au centre
- **Injection de Dépendances Sophistiquée** : Couplage ultra-faible
- **Configuration Découplée Avancée** : Flexibilité maximale des comportements IA

### 🔬 Qualité Technique
- **Typage Complet** : Type hints exhaustifs avec validation
- **Gestion d'Erreurs Robuste** : Mécanismes de retry et recovery
- **Tests Complets** : Couverture élevée avec tests de plusieurs niveaux
- **Documentation Code** : Docstrings français détaillées

### 🚀 Innovation IA
- **RAG Multimodal Avancé** : Combine recherche vectorielle + images + texte
- **Pipeline de Traitement Sophistiqué** : OCR + Description + Labelling en parallèle
- **Configuration IA Découplée** : Paramétrage fin des comportements de l'agent
- **Traçabilité Complète** : Sources et confiance pour chaque réponse IA

### ☁️ Intégration Cloud
- **Azure-Native** : Exploitation optimale des services managés
- **Stockage Organisé** : Structure de dossiers logique et scalable  
- **Sécurité Renforcée** : JWT + sessions + permissions granulaires
- **Monitoring Intégré** : Logs détaillés et debugging avancé

Ce projet représente un **exemple d'excellence** en termes d'architecture moderne, d'intégration IA avancée et de qualité de développement. Il démontre une maîtrise approfondie des patterns d'architecture propre, des technologies Azure, et des techniques d'IA conversationnelle avec RAG multimodal.