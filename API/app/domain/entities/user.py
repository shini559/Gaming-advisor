from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class User:
    """A user"""

    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    hashed_password: str
    is_active: bool = True
    is_subscribed: bool = False
    is_admin: bool = False
    token_credits: int = 0
    avatar: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        hashed_password: str,
        token_credits: int = 0,
        avatar: Optional[str] = None,
        is_admin: bool = False
    ) -> "User":
        """Factory method to create a new user"""
        return cls(
            id=uuid4(),
            username=username.lower().strip(),
            email=email.lower().strip(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            hashed_password=hashed_password,
            is_active=True,
            is_subscribed=False,
            is_admin=is_admin,
            token_credits=token_credits,
            avatar=avatar,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def activate(self) -> None:
        """Activates user account"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivates user account"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)