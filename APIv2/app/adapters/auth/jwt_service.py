from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from uuid import UUID

from config import settings


class JWTService:
    """Service for JWT token generation and validation"""
    
    def __init__(self):
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_token_expire_minutes = settings.jwt_access_token_expire_minutes
    
    def create_access_token(self, user_id: UUID, username: str, email: str) -> str:
        """Create JWT access token for user"""
        expires_delta = timedelta(minutes=self._access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),  # Subject (user ID)
            "username": username,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access_token"
        }
        
        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None:
                return None
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                return None
            
            # Check token type
            if payload.get("type") != "access_token":
                return None
            
            return payload
            
        except JWTError:
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[UUID]:
        """Extract user ID from token"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        try:
            return UUID(user_id_str)
        except ValueError:
            return None
    
    def get_username_from_token(self, token: str) -> Optional[str]:
        """Extract username from token"""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        return payload.get("username")