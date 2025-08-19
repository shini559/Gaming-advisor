from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Optional
import uuid
import aiofiles
from pathlib import Path

from app.config import settings
from app.services.analyzer import analyze_rulebook
from app.services.cache import game_cache

router = APIRouter(prefix = "/api/v1/games", tags=["Games"])

# Dossier pour stocker les uploads
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_game_rulebook(
    file: UploadFile = File(...),
    game_name: Optional[str] = None
):
    """
    Upload un livret de règles (PDF ou image)

    Args:
        - **file**: Le fichier PDF ou image du livret
        - **game_name**: Nom du jeu (optionnel, détecté automatiquement sinon)
    """
    
    # Validation du type de fichier
    allowed_types = ["application/pdf", "image/jpg", "image/png", "image/jpeg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code = 400,
            detail = "Type de fichier non supporté. Acceptés : PDF, JPEG, PNG"
        )
        
    # Validation de la taille
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code = 400,
            detail = f"Fichier trop volumineux. Max : {settings.max_file_size // (1024*1024)}MB"
        )
        
    # Génération d'un ID unique pour ce jeu
    game_id = str(uuid.uuid4())
    
    # Création du nom de fichier
    file_extension = Path(file.filename).suffix
    filename = f"{game_id}{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    try:
        #Sauvegarde asynchrone du fichier
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
            
        # Analyse du fichier
        analysis = analyze_rulebook(file_path)
        game_cache.store_analysis(game_id, analysis)
            
        return {
            "game_id": game_id,
            "filename": filename,
            "file_size": file.size,
            "content_type": file.content_type,
            "analysis": analysis,
            "message": "Upload et analyse terminés"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"Erreur lors de l'upload: {str(e)}"
            )
        
@router.post("/{game_id}/ask")
async def ask_question(game_id: str, question: str):
    """
    Pose une question sur les règles d'un jeu

    Args:
        game_id (str): L'ID du jeu (obtenu lors de l'upload)
        question (str): La question sur les règles
    """
    
    # Vérifie si le jeu existe dans le cache
    if not game_cache.exists(game_id):
        raise HTTPException(
            status_code = 404,
            detail = "Jeu non trouvé. Uploadez d'abord le livret."
        )
        
    # Récupère l'analyse du cache
    analysis = game_cache.get_analysis(game_id)
    
    # Pour l'instant, réponse simple (on améliorerait avec l'IA)
    return {
        "game_id": game_id,
        "question": question,
        "answer": f"Voici ma réponse sur {analysis['data']['game_name']}: {question}",
        "context": analysis['data']['rules'][:2] #2 premières règles
    }

@router.get("/{game_id}/status")
async def get_name_status(game_id: str):
    """
    Récupère le statut d'analyse d'un jeu
    """
    return {
        "game_id": game_id,
        "status": "processing",
        "message": "Analyse en cours..."
    }
    
@router.get("/debug/cache")
async def debug_cache():
    """Route temporaire pour voir le contenu du cache"""
    return {
        "cache_size": len(game_cache.analyses),
        "game_ids": list(game_cache.analyses.keys())
    }