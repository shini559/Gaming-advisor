from abc import ABC, abstractmethod
from datetime import datetime
from typing import Tuple
from uuid import UUID


class IJWTService(ABC):
    """Interface pour les services de gestion des tokens JWT"""

    @abstractmethod
    def create_token_pair(self, user_id: UUID, username: str, email: str) -> Tuple[str, str, str, int, int]:
        """
        Crée une paire de tokens (access + refresh)

        Returns:
            Tuple[access_token, refresh_token, refresh_token_hash, access_expires_in, refresh_expires_in]
        """
        pass

    @abstractmethod
    def get_refresh_token_expiry(self) -> datetime:
        """Obtient la date d'expiration pour un refresh token"""
        pass

    @abstractmethod
    def verify_access_token(self, token: str) -> dict:
        """Vérifie et décode un access token"""
        pass

    @abstractmethod
    def verify_refresh_token(self, refresh_token: str, stored_hash: str) -> dict:
        """Vérifie et décode un refresh token"""
        pass

    @abstractmethod
    def get_user_id_from_token(self, token: str) -> UUID:
        """Obtient l'ID utilisateur d'un token"""
        pass

    @abstractmethod
    def _generate_refresh_token(self) -> str:
        """Génére un refresh token sécurisé"""
        pass

    @abstractmethod
    def hash_refresh_token(self, refresh_token: str) -> str:
        """Hashe un refresh token pour le stockage"""
        pass