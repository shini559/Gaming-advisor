from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from app.auth.service import decode_access_token, get_user
from app.auth.models import User

# Configuration OAuth2 - pointe vers notre endpoint de login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency qui vérifie le token JWT et retourne l'utilisateur courant

    Args:
        token (str, optional): JWT token extrait automatiquement du header Authorization

    Returns:
        User: Utilisateur authentifié
        
    Raises:
        HTTPException: Si token invalide ou utilisateur introuvable
    """

    # Excpetion personalisée pour les erreurs d'auth
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW_Authenticate": "Bearer"},
    )
    
    try:
        # Décodage du token JWT
        token_data = decode_access_token(token)
        if token_data is None or token_data.email is None:
            raise credentials_exception
        
    except Exception:
        raise credentials_exception
    
    # Récupération de l'utilisateur
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    
    # Vérification que l'utilisateur est acitf
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
        
    return user

def get_current_active_admin(current_user : User = Depends(get_current_user)) -> User:
    """
    Dependency pour les routes admin seulement

    Utilise get_current_user puis vérifie le rôle admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
        
    return current_user