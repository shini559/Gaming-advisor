from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class User:
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    hashed_password: str
    is_active: bool = True
    is_subscribed: bool = False
    credits: int = 0
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
        credits: int = 0,
        avatar: Optional[str] = None
    ) -> "User":
        """Create a new user with default values"""
        now = datetime.utcnow()
        return cls(
            id=uuid4(),
            username=username.lower().strip(),
            email=email.lower().strip(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            hashed_password=hashed_password,
            is_active=True,
            is_subscribed=False,
            credits=credits,
            avatar=avatar,
            created_at=now,
            updated_at=now
        )
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def subscribe(self) -> None:
        """Subscribe user"""
        self.is_subscribed = True
        self.updated_at = datetime.utcnow()
    
    def unsubscribe(self) -> None:
        """Unsubscribe user"""
        self.is_subscribed = False
        self.updated_at = datetime.utcnow()
    
    def add_credits(self, amount: int) -> None:
        """Add credits to user account"""
        if amount <= 0:
            raise ValueError("Cannot add negative credits")
        self.credits += amount
        self.updated_at = datetime.utcnow()
    
    def consume_credits(self, amount: int) -> bool:
        """Consume credits from user account. Returns True if successful."""
        if amount <= 0:
            raise ValueError("No credits available")
        if self.credits < amount:
            self.credits = 0
        self.credits -= amount
        self.updated_at = datetime.utcnow()
        return True