from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    api_title: str = "GameAdvisor API"
    api_version: str = "0.0.1"
    debug: bool = False
    
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
    jwt_secret_key: str = "CHANGE-ME-IN-PRODUCTION-USE-STRONG-256-BIT-KEY"
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
    image_max_file_size_mb: int = 1
    image_max_width: int = 1000
    image_max_height: int = 1000
    image_allowed_formats: list[str] = ["jpg", "jpeg", "png"]
    image_processing_resolution: tuple[int, int] = (1024, 1024)

    # Queue Configuration
    redis_url: str = "redis://localhost:6379/0"
    queue_retry_attempts: int = 3
    queue_retry_delay_seconds: int = 30
    queue_processing_timeout_seconds: int = 300

    # Batch Processing Configuration
    batch_max_retries: int = 3
    batch_parallel_workers: int = 5
    batch_retry_delay_minutes: int = 5

    # AI Processing Prompts
    ocr_prompt: str = """Extracte tout le texte visible dans cette image de règles de jeu de société.
     Conserve la structure et la hiérarchie du texte. Ignore les éléments purement décoratifs."""

    vision_description_prompt: str = """Décris précisément les éléments visuels de cette image de jeu de société:
     - Type de contenu (plateau, cartes, pions, règles)
     - Éléments de gameplay visibles
     - Couleurs et motifs principaux
     - Symboles et icônes
     - Style artistique
     Sois concis mais détaillé."""

    vision_labeling_prompt: str = """Identifie et labellise tous les composants de jeu visibles:
     - board, cards, tokens, dice, meeples, miniatures
     - text, rules, icons, symbols
     - ui_elements, score_tracks, player_aids
     Retourne une liste de labels séparés par des virgules."""


    
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