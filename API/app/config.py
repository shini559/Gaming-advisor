from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
	# API Configuration
	api_title: str = "GameAdvisor API"
	api_version: str = "1.0.0"
	debug: bool = True

	# Database Configuration (Azure PostgreSQL)      
	db_host: Optional[str] = None
	db_user: Optional[str] = None
	db_password: Optional[str] = None
	db_name: Optional[str] = None
	db_port: int = 5432
	db_ssl_mode: str = "require"

	# AI Models
	openai_api_key: Optional[str] = None
	anthropic_api_key: Optional[str] = None
	subscription_key: Optional[str] = None  # Azure subscription key

	# File Storage
	upload_dir: str = "uploads"
	max_file_size: int = 50 * 1024 * 1024  # 50MB

	# JWT Configuration
	jwt_secret_key: Optional[str] = None
	jwt_algorithm: str = "HS256"
	jwt_access_token_expire_minutes: int = 30

	@property
	def database_url(self) -> Optional[str]:
		"""Construit l'URL de connexion PostgreSQL Azure"""
		if not all([self.db_host, self.db_user, self.db_password, self.db_name]):
			return None
		return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?ssl={self.db_ssl_mode}"

	class Config:
		env_file = ".env"
		extra = "ignore"  # Ignore les variables d'environnement supplémentaires

settings = Settings()