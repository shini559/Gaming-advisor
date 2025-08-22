import hashlib
import secrets
from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from jose import jwt, JWTError

from app.shared.utils.datetime_utils import utc_now
from config import settings


class JWTService:
    """Service pour la génération et validation des tokens JWT"""

    def __init__(self):
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self._refresh_token_expire_days = getattr(settings, 'jwt_refresh_token_expire_days', 30)

    def create_token_pair(self, user_id: UUID, username: str, email: str) -> Tuple[str, str, str, int, int]:
        """Créer une paire access token + refresh token"""
        # Créer l'access token
        access_token = self.create_access_token(user_id, username, email)

        # Créer le refresh token
        refresh_token = self._generate_refresh_token()
        refresh_token_hash = self._hash_refresh_token(refresh_token)

        # Calculer les durées d'expiration
        access_expires_in = self._access_token_expire_minutes * 60  # en secondes
        refresh_expires_in = self._refresh_token_expire_days * 24 * 60 * 60  # en secondes

        return access_token, refresh_token, refresh_token_hash, access_expires_in, refresh_expires_in

    def create_access_token(self, user_id: UUID, username: str, email: str) -> str:
        """Créer un JWT access token pour l'utilisateur"""
        expires_delta = timedelta(minutes=self._access_token_expire_minutes)
        expire = utc_now() + expires_delta

        to_encode = {
            "sub": str(user_id),  # Subject (user ID)
            "username": username,
            "email": email,
            "exp": expire,
            "iat": utc_now(),
            "type": "access_token"
        }

        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifier et décoder un JWT token"""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

            # Vérifier si le token est expiré
            exp = payload.get("exp")
            if exp is None:
                return None

            if utc_now() > datetime.fromtimestamp(exp, tz=timezone.utc):
                return None

            # Vérifier le type de token
            if payload.get("type") != "access_token":
                return None

            return payload

        except JWTError:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[UUID]:
        """Extraire l'ID utilisateur du token"""
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
        """Extraire le nom d'utilisateur du token"""
        payload = self.verify_token(token)
        if payload is None:
            return None

        return payload.get("username")

    def get_refresh_token_expiry(self) -> datetime:
        """Obtenir la date d'expiration pour un nouveau refresh token"""
        return utc_now() + timedelta(days=self._refresh_token_expire_days)

    def _generate_refresh_token(self) -> str:
        """Générer un refresh token sécurisé"""
        return secrets.token_urlsafe(64)

    def _hash_refresh_token(self, refresh_token: str) -> str:
        """Hasher un refresh token pour le stockage"""
        return hashlib.sha256(refresh_token.encode()).hexdigest()

    def verify_refresh_token(self, refresh_token: str, stored_hash: str) -> bool:
        """Vérifier qu'un refresh token correspond au hash stocké"""
        token_hash = self._hash_refresh_token(refresh_token)
        return secrets.compare_digest(token_hash, stored_hash)