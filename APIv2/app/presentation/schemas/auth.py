from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserRegistrationRequest(BaseModel):
    """Schema pour la requête d'inscription utilisateur"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    avatar: Optional[str] = Field(None, max_length=500, description="Avatar URL or base64 string (optional)")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "secure_password123",
                "avatar": "https://example.com/avatar.jpg"
            }
        }
    )


class UserResponse(BaseModel):
    """Schema pour la réponse utilisateur"""
    user_id: str = Field(..., description="User unique identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    is_active: bool = Field(..., description="Whether the user account is active")
    credits: int = Field(..., description="User credits balance")
    avatar: Optional[str] = Field(None, description="User avatar URL or base64 string")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "credits": 100,
                "avatar": "https://example.com/avatar.jpg"
            }
        }
    )

class UserLoginRequest(BaseModel):
    """Schema pour la requête de connexion utilisateur (compatible OAuth2)"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information (optional)")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "secure_password123",
                "device_info": {
                    "device_type": "web",
                    "browser": "Chrome 120",
                    "os": "Windows 11"
                }
            }
        }
    )

class TokenResponse(BaseModel):
    """Schema pour la réponse de token OAuth2"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token for renewing access")
    token_type: str = Field(..., description="Token type (bearer)")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "def50200ab1c...",
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_expires_in": 2592000,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john.doe@example.com"
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Schema pour la requête de rafraîchissement de token"""
    refresh_token: str = Field(..., description="Refresh token")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Updated device information (optional)")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "refresh_token": "def50200ab1c...",
                "device_info": {
                    "last_activity": "2024-01-20T10:30:00Z"
                }
            }
        }
    )

class LogoutRequest(BaseModel):
    """Schema pour la requête de déconnexion"""
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke (optional)")
    session_id: Optional[UUID] = Field(None, description="Specific session ID to revoke (optional)")
    logout_all: bool = Field(False, description="Logout from all sessions")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "refresh_token": "def50200ab1c...",
                "logout_all": False
            }
        }
    )

class LogoutResponse(BaseModel):
    """Schema pour la réponse de déconnexion"""
    success: bool = Field(..., description="Whether logout was successful")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")
    message: str = Field(..., description="Status message")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "success": True,
                "sessions_revoked": 1,
                "message": "Successfully logged out"
            }
        }
    )

class UserSessionResponse(BaseModel):
    """Schema pour la réponse de session utilisateur"""
    session_id: str = Field(..., description="Session ID")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information")
    created_at: str = Field(..., description="Session creation timestamp")
    last_used_at: str = Field(..., description="Last activity timestamp")
    expires_at: str = Field(..., description="Session expiration timestamp")
    is_current: bool = Field(..., description="Whether this is the current session")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "device_info": {
                    "device_type": "web",
                    "browser": "Chrome 120",
                    "os": "Windows 11"
                },
                "created_at": "2024-01-20T10:00:00Z",
                "last_used_at": "2024-01-20T10:30:00Z",
                "expires_at": "2024-02-20T10:00:00Z",
                "is_current": True
            }
        }
    )

class ErrorResponse(BaseModel):
    """Schema pour les réponses d'erreur"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for client handling")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "detail": "User with this email already exists",
                "error_code": "USER_ALREADY_EXISTS"
            }
        }
    )