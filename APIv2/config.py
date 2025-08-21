from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    api_title: str = "GameAdvisor API v2"
    api_version: str = "2.0.0"
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
settings = Settings()