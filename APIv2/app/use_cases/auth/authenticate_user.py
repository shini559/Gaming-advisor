from dataclasses import dataclass
from typing import Optional

from app.domain.entities.user import User
from app.domain.ports.repositories.user_repository import IUserRepository
from app.adapters.auth.password_service import PasswordService
from app.adapters.auth.jwt_service import JWTService


@dataclass
class AuthenticateUserRequest:
    """Request DTO for user authentication"""
    username_or_email: str
    password: str


@dataclass
class AuthenticateUserResponse:
    """Response DTO for user authentication"""
    access_token: str
    token_type: str
    user_id: str
    username: str
    email: str
    expires_in: int


class InvalidCredentialsError(Exception):
    """Raised when user credentials are invalid"""
    pass


class UserNotActiveError(Exception):
    """Raised when user account is not active"""
    pass


class AuthenticateUser:
    """Use case for user authentication"""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: PasswordService,
        jwt_service: JWTService
    ):
        self._user_repository = user_repository
        self._password_service = password_service
        self._jwt_service = jwt_service
    
    async def execute(self, request: AuthenticateUserRequest) -> AuthenticateUserResponse:
        """Execute user authentication"""
        
        # Validate input
        self._validate_request(request)
        
        # Find user by email or username
        user = await self._find_user(request.username_or_email)
        if not user:
            raise InvalidCredentialsError("Invalid username/email or password")
        
        # Check if user is active
        if not user.is_active:
            raise UserNotActiveError("User account is deactivated")
        
        # Verify password
        if not self._password_service.verify_password(request.password, user.hashed_password):
            raise InvalidCredentialsError("Invalid username/email or password")
        
        # Generate JWT token
        access_token = self._jwt_service.create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
        # Return response
        return AuthenticateUserResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            expires_in=self._jwt_service._access_token_expire_minutes * 60  # in seconds
        )
    
    async def _find_user(self, username_or_email: str) -> Optional[User]:
        """Find user by username or email"""
        # Try to find by email first
        if "@" in username_or_email:
            user = await self._user_repository.find_by_email(username_or_email)
            if user:
                return user
        
        # Try to find by username
        return await self._user_repository.find_by_username(username_or_email)
    
    def _validate_request(self, request: AuthenticateUserRequest) -> None:
        """Validate authentication request"""
        errors = []
        
        if not request.username_or_email or len(request.username_or_email.strip()) == 0:
            errors.append("Username or email is required")
        
        if not request.password or len(request.password) == 0:
            errors.append("Password is required")
        
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")