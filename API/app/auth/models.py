from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Modèle pour recevoir les données de login
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
# Modèle pour créer un utilisateur (si on ajoute register plus tard)
class Usercreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
# Modèle pour l'utilisateur en base/cache (sans password!)
class User(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: Optional[datetime] = None
    
# Modèle pour la réponse JWT
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int # en secondes
    
# Modèle pour les données dans le JWT payload
class TokenData(BaseModel):
    email: Optional[str] = None
    exp: Optional[int] = None # timestamp expiration