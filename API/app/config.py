from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
	# API Configuration\
	api_title: str = "GameAdvisor API"
	api_version: str = "1.0.0"
	debug: bool = True

	# AI Models
	openai_api_key: Optional[str] = None
	anthropic_api_key: Optional[str] = None

	# File Storage
	upload_dir: str = "uploads"
	max_file_size: int = 50 * 1024 * 1024 #50MB

	class Config:
		env_file = ".env"

settings = Settings()
