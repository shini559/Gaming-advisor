from dataclasses import dataclass
from typing import Optional

from app.domain.entities.user import User
from app.domain.ports.repositories.user_repository import IUserRepository
from app.adapters.auth.password_service import PasswordService


@dataclass
class RegisterUserRequest:
    """Request DTO for user registration"""
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    avatar: Optional[str] = None


@dataclass
class RegisterUserResponse:
    """Response DTO for user registration"""
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    credits: int
    avatar: Optional[str] = None


class UserAlreadyExistsError(Exception):
    """Raised when trying to register a user that already exists"""
    pass


class RegisterUser:
    """Use case for user registration"""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: PasswordService
    ):
        self._user_repository = user_repository
        self._password_service = password_service
    
    async def execute(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """Execute user registration"""

        # Validate input
        self._validate_request(request)

        # Check if user already exists
        if await self._user_repository.exists_by_email(request.email):
            raise UserAlreadyExistsError(f"User with email '{request.email}' already exists")

        if await self._user_repository.exists_by_username(request.username):
            raise UserAlreadyExistsError(f"User with username '{request.username}' already exists")

        # Hash password
        hashed_password = self._password_service.hash_password(request.password)

        # Create user entity
        user = User.create(
            username=request.username,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            hashed_password=hashed_password,
            credits=100,
            avatar=request.avatar
        )

        # Save user
        saved_user = await self._user_repository.save(user)

        # Return response
        return RegisterUserResponse(
            user_id=str(saved_user.id),
            username=saved_user.username,
            email=saved_user.email,
            first_name=saved_user.first_name,
            last_name=saved_user.last_name,
            is_active=saved_user.is_active,
            credits=saved_user.credits,
            avatar=saved_user.avatar
        )

    def _validate_request(self, request: RegisterUserRequest) -> None:
        """Validate registration request"""
        errors = []
        
        if not request.username or len(request.username.strip()) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if not request.email or "@" not in request.email:
            errors.append("Valid email is required")
        
        if not request.first_name or len(request.first_name.strip()) < 1:
            errors.append("First name is required")
        
        if not request.last_name or len(request.last_name.strip()) < 1:
            errors.append("Last name is required")
        
        if not request.password or len(request.password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")