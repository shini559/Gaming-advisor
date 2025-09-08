from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from uuid import UUID, uuid4


@dataclass
class UserSession:
    """User session"""

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
        """Creates a new user session"""

        return cls(
            id=uuid4(),
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            device_info=device_info or {},
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
            is_active=True
        )

    def update_last_used(self) -> None:
        """Updates last used time"""
        self.last_used_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivates session"""
        self.is_active = False

    def is_expired(self) -> bool:
        """Checks if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Checks if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired()