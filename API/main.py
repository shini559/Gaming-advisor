from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.config import settings
from app.api.games import router as games_router
from app.api.auth import router as auth_router

# Création de l'application FastAPI
app = FastAPI(
	title = settings.api_title,
	version = settings.api_version,
	description = "API pour analyser les livrets de règles de jeux avec IA",
	docs_url = "/docs",
	redoc_url = "/redoc"
)

# Configuration CORS (pour les appels depuis le frontend)
app.add_middleware(
	CORSMiddleware,
	allow_origins = ["*"], # En production, spécifier les domaines autorisés
	allow_credentials = True,
	allow_methods = ["*"],
	allow_headers = ["*"],
)

# Inclusion des routes
app.include_router(games_router)
app.include_router(auth_router)

# Modèles Pydantic pour la validation des données
class GameResponse(BaseModel):
	id: str
	name: str
	status: str
	message: str

class QuestionRequest(BaseModel):
	question: str
	game_id: str

# Route de santé pour monitoring
@app.get("/health")
async def health_check():
	return {
	"message": "GameAdvisor API is running!",
	"version": settings.api_version,
	"docs": "/docs"
}

if __name__ == "__main__":
	uvicorn.run(
		"main:app",
		host = "0.0.0.0",
		port = 8000,
		reload = settings.debug
	)