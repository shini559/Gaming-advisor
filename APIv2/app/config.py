from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    api_title: str = "GameAdvisor API"
    api_version: str = "0.0.1"
    debug: bool = True
    sql_debug: bool = True
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database Configuration (Azure PostgreSQL)
    db_host: Optional[str] = None
    db_port: int = 5432
    db_name: Optional[str] = None
    db_username: Optional[str] = None
    db_password: Optional[str] = None
    db_ssl_mode: str = "require"
    
    # JWT Configuration
    jwt_secret_key: str = "DEVELOPMENT-KEY"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 240
    jwt_refresh_token_expire_days: int = 7

    # Azure Blob Storage Configuration
    azure_storage_account: Optional[str] = None
    azure_storage_key: Optional[str] = None
    azure_storage_connection_string: Optional[str] = None
    azure_blob_container_name: str = "gameadvisorstorage"

    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    
    # Vision Model Configuration
    azure_openai_vision_api_version: Optional[str] = None
    azure_openai_vision_deployment: Optional[str] = None
    
    # Embedding Model Configuration
    azure_openai_embedding_api_version: Optional[str] = None
    azure_openai_embedding_deployment: Optional[str] = None
    azure_openai_embedding_dimensions: int = 1536

    # Image Processing Configuration
    image_max_file_size_mb: int = 5
    image_max_width: int = 1000
    image_max_height: int = 1000
    image_allowed_formats: list[str] = ["jpg", "jpeg"]
    image_processing_resolution: tuple[int, int] = (1024, 1024)

    # Queue Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_host: Optional[str] = None
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    queue_retry_attempts: int = 3
    queue_retry_delay_seconds: int = 30
    queue_processing_timeout_seconds: int = 300
    redis_ttl: int = 24 # Time before deleting job data (in hours)

    # Batch Processing Configuration
    batch_max_retries: int = 3
    batch_parallel_workers: int = 5
    batch_retry_delay_minutes: int = 5
    
    # AI Processing Methods (toggles)
    enable_ocr: bool = True                 # Activer extraction OCR
    enable_visual_description: bool = True  # Activer description visuelle
    enable_labeling: bool = True           # Activer métadonnées JSON
    search_method: str = "description"          # "ocr" | "description" | "labels" | "hybrid"

    # AI Processing Prompts
    ocr_prompt: str = """Extracte tout le texte visible dans cette image de règles de jeu de société.
     Conserve la structure et la hiérarchie du texte. Ignore les éléments purement décoratifs."""

    vision_description_prompt: str = """Analyse cette page de règles de jeu:

1. TEXTE: Extrait tout le texte visible
2. SCHÉMAS: Décris précisément tous diagrammes, tableaux, illustrations
3. ÉLÉMENTS: Identifie et décris précisemment les composants (cartes, pions, dés, plateau, etc.)
4. RÈGLES: Extrait les règles et mécaniques spécifiques
5. SECTIONS: Catégorise (setup/mise en place, tour de jeu, scoring/points, fin de partie)

Format ta réponse en JSON:
{
    "text_content": "texte intégral visible",
    "diagrams": [{"type": "tableau|schéma|illustration", "description": "..."}],
    "game_elements": ["cartes", "jetons", ...],
    "rules": [{"rule": "règle spécifique", "context": "contexte"}],
    "sections": [{"title": "...", "type": "setup|gameplay|scoring|endgame", "content": "..."}]
}"""

    vision_labeling_prompt: str = """Analyse cette page de règles de jeu et extrait des métadonnées structurées en anglais:

1. ÉLÉMENTS: Liste tous les composants de jeu visibles (cartes, pions, dés, plateau, jetons, etc.)
2. SCHÉMAS: liste tous les diagrammes, tableaux, illustrations avec ce qu'ils représentent
3. ACTIONS: Identifie toutes les actions/mécaniques mentionnées (placer, déplacer, piocher, etc.)
4. CONCEPTS: Extrait les concepts clés (points, tours, victoire, setup, etc.)
5. SECTIONS: Catégorise le contenu (setup, gameplay, scoring, endgame)

Format JSON structuré pour la recherche:
{
    "game_elements": ["composant1", "composant2", ...],
    "diagrams": [{"type": "type", "description": "description détaillée", "elements": ["elem1", "elem2"]}],
    "game_actions": ["action1", "action2", ...],
    "key_concepts": ["concept1", "concept2", ...],
    "sections": [{"title": "titre", "type": "setup|gameplay|scoring|endgame", "keywords": ["mot1", "mot2"]}],
    "searchable_text": "résumé textuel pour recherche sémantique"
}"""

    # Agent IA Configuration
    vector_search_top_k: int = 5
    vector_similarity_threshold: float = 0.1
    agent_max_context_length: int = 8000
    agent_max_conversation_history: int = 20
    
    # Chat Configuration
    chat_conversation_timeout_hours: int = 24
    chat_max_title_length: int = 100
    chat_default_title: str = "Nouvelle conversation"
    
    # Agent IA Prompts
    agent_system_prompt: str = '''You are a game master & boardgame assistant. Your role is to assist board gamers in setting up their games, understanding the rules, calculate the score.

The users will send you data. You will analyze this data and use it to answer their questions. ONLY USE THE DATA THEY PROVIDE TO ANSWER THEIR QUESTIONS! YOU MUST NEVER ANSWER A QUESTION ABOUT GAME RULES IF YOU HAVE NOT BEEN PROVIDED DATA BY THE USER!

Answer questions clearly and directly. Use simple French. Ask questions if you need clarification.'''

    
    def __post_init__(self):
        """Validate critical security settings"""
        if self.jwt_secret_key == "CHANGE-ME-IN-PRODUCTION-USE-STRONG-256-BIT-KEY":
            import warnings
            warnings.warn("⚠️ Using default JWT secret key! Set JWT_SECRET_KEY in production!")
        
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
    
    @property
    def database_url(self) -> Optional[str]:
        """Construct PostgreSQL connection URL for Azure"""
        if not all([self.db_host, self.db_username, self.db_password, self.db_name]):
            return None
        return f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?ssl={self.db_ssl_mode}"

    @property
    def azure_blob_url(self) -> Optional[str]:
        """Construct Azure Blob Storage URL"""
        if not self.azure_storage_account:
            return None
        return f"https://{self.azure_storage_account}.blob.core.windows.net"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Create global settings instance
settings = Settings()