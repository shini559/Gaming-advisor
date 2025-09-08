import hashlib
import secrets
from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from uuid import UUID

from jose import jwt, JWTError

from app.config import settings
from app.domain.ports.services.jwt_service import IJWTService


class JWTService(IJWTService):
    """JWT token generation & validation service"""

    def __init__(self) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self._refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def create_token_pair(self, user_id: UUID, username: str, email: str) -> Tuple[str, str, str, int, int]:
        """Creates an access token + refresh token pair"""

        access_token = self._create_access_token(user_id, username, email)

        refresh_token = self._generate_refresh_token()
        refresh_token_hash = self.hash_refresh_token(refresh_token)

        # Calculate expiration (in seconds)
        access_expires_in = self._access_token_expire_minutes * 60
        refresh_expires_in = self._refresh_token_expire_days * 86400

        return access_token, refresh_token, refresh_token_hash, access_expires_in, refresh_expires_in

    def _create_access_token(self, user_id: UUID, username: str, email: str) -> str:
        """Creates an access token"""

        expires_delta = timedelta(minutes=self._access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": str(user_id),  # Subject
            "username": username,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc), # Issued at
            "type": "access_token"
        }

        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded_jwt

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifies and decodes an access JWT token"""

        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

            # Check if the token expired
            exp = payload.get("exp")
            if exp is None:
                return None

            if datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
                return None

            # Check the token type
            if payload.get("type") != "access_token":
                return None

            return payload

        except JWTError:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[UUID]:
        """Extracts user ID from token"""

        payload = self.verify_access_token(token)
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
        """Extraire le nom d'utilisateur du token"""
        payload = self.verify_access_token(token)
        if payload is None:
            return None

        return payload.get("username")

    def get_refresh_token_expiry(self) -> datetime:
        """Obtenir la date d'expiration pour un nouveau refresh token"""
        return datetime.now(timezone.utc) + timedelta(days=self._refresh_token_expire_days)

    def _generate_refresh_token(self) -> str:
        """Générer un refresh token sécurisé"""
        return secrets.token_urlsafe(64)

    def hash_refresh_token(self, refresh_token: str) -> str:
        """Hasher un refresh token pour le stockage"""
        return hashlib.sha256(refresh_token.encode()).hexdigest()

    def verify_refresh_token(self, refresh_token: str, stored_hash: str) -> bool:
        """Vérifier qu'un refresh token correspond au hash stocké"""
        token_hash = self.hash_refresh_token(refresh_token)
        return secrets.compare_digest(token_hash, stored_hash)