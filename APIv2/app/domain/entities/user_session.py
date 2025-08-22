from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID, uuid4

from app.shared.utils.datetime_utils import utc_now


@dataclass
class UserSession:
    """Entité métier représentant une session utilisateur"""
    id: UUID
    user_id: UUID
    refresh_token_hash: str
    device_info: Optional[Dict[str, Any]]
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime
    is_active: bool

    @classmethod
    def create(
        cls,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        device_info: Optional[Dict[str, Any]] = None
    ) -> "UserSession":
        """Créer une nouvelle session utilisateur"""
        now = utc_now()
        return cls(
            id=uuid4(),
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            device_info=device_info or {},
            expires_at=expires_at,
            created_at=now,
            last_used_at=now,
            is_active=True
        )

    def update_last_used(self) -> None:
        """Mettre à jour la dernière utilisation"""
        self.last_used_at = utc_now()

    def deactivate(self) -> None:
        """Désactiver la session"""
        self.is_active = False

    def is_expired(self) -> bool:
        """Vérifier si la session est expirée"""
        return utc_now() > self.expires_at

    def is_valid(self) -> bool:
        """Vérifier si la session est valide (active et non expirée)"""
        return self.is_active and not self.is_expired()