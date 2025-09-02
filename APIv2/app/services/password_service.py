from passlib.context import CryptContext

from app.domain.ports.services.password_service import IPasswordService


class PasswordService(IPasswordService):
    """Service for password hashing and verification"""
    
    def __init__(self) -> None:
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hashes a password"""

        return self._pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a password against its hash"""

        return self._pwd_context.verify(plain_password, hashed_password)