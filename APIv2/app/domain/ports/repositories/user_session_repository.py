from abc import abstractmethod, ABC
from typing import List, Optional
from uuid import UUID

from app.domain.entities.user_session import UserSession


class IUserSessionRepository(ABC):
    """Interface pour le repository des sessions utilisateur"""

    @abstractmethod
    async def save(self, session: UserSession) -> UserSession:
        """Sauvegarder une session"""
        pass

    @abstractmethod
    async def find_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Trouver une session par son ID"""
        pass

    @abstractmethod
    async def find_by_refresh_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Trouver une session par le hash du refresh token"""
        pass

    @abstractmethod
    async def find_active_by_user_id(self, user_id: UUID) -> List[UserSession]:
        """Trouver toutes les sessions actives d'un utilisateur"""
        pass

    @abstractmethod
    async def deactivate_session(self, session_id: UUID) -> bool:
        """Désactiver une session spécifique"""
        pass

    @abstractmethod
    async def deactivate_all_user_sessions(self, user_id: UUID) -> int:
        """Désactiver toutes les sessions d'un utilisateur"""
        pass

    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Nettoyer les sessions expirées"""
        pass

    @abstractmethod
    async def count_active_sessions_for_user(self, user_id: UUID) -> int:
        """Compter les sessions actives d'un utilisateur"""
        pass