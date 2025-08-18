from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.auth.models import User, TokenData

# Configuration pour hasher les passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clé secrète pour signer les JWT (en production: variable d'environnement)
SECRET_KEY = "votre-clé-super-secrète-à-changer-en-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Base d'utilisateurs simple (remplacée par DB plus tard)
fake_users_db = {
    "admin@gameadvisor.com": {
        "email": "admin@gameadvisor.com",
        "full_name": "Admin GameAdvisor",
        "role": "admin",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", # secret
        "is_active": True
    },
    "user@gameadvisor.com": {
        "email": "user@gameadvisor.com",
        "full_name": "User GameAdvisor",
        "role": "user",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", # secret
        "is_active": True
    }
}

def verify_password(plain_password: str, hashed_password: str) -> str:
    """Vérifie si le password correspond au hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Génère le hash d'un password"""
    return pwd_context.hash(password)

def get_user(email: str) -> Optional[User]:
    """Récupère un utilisateur par email"""
    if email in fake_users_db:
        user_dict = fake_users_db[email]
        return User(**user_dict)
    return None

def authenticate_user(email: str, password: str) -> Optional[User]:
    user_dict = fake_users_db.get(email)
    if not user_dict:
        return None
    if not verify_password(password, user_dict["hashed_password"]):
        return None
    return User(**user_dict)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    """Décode et valide un JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email, exp=payload.get("exp"))
        return token_data
    except JWTError:
        return None