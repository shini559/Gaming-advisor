from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.web.schemas.auth import (
    UserRegistrationRequest, UserResponse, UserLoginRequest, TokenResponse, ErrorResponse
)
from app.adapters.database.connection import get_async_session
from app.adapters.database.repositories.user_repository import UserRepository
from app.adapters.auth.password_service import PasswordService
from app.adapters.auth.jwt_service import JWTService
from app.use_cases.auth.register_user import RegisterUser, RegisterUserRequest, UserAlreadyExistsError
from app.use_cases.auth.authenticate_user import (
    AuthenticateUser, AuthenticateUserRequest, InvalidCredentialsError, UserNotActiveError
)
from app.adapters.web.dependencies.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_password_service() -> PasswordService:
    """Dependency to get password service"""
    return PasswordService()


def get_jwt_service() -> JWTService:
    """Dependency to get JWT service"""
    return JWTService()


async def get_register_user_use_case(
    db: AsyncSession = Depends(get_async_session),
    password_service: PasswordService = Depends(get_password_service)
) -> RegisterUser:
    """Dependency to get RegisterUser use case"""
    user_repository = UserRepository(db)
    return RegisterUser(user_repository, password_service)


async def get_authenticate_user_use_case(
    db: AsyncSession = Depends(get_async_session),
    password_service: PasswordService = Depends(get_password_service),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> AuthenticateUser:
    """Dependency to get AuthenticateUser use case"""
    user_repository = UserRepository(db)
    return AuthenticateUser(user_repository, password_service, jwt_service)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "User already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Register a new user",
    description="Create a new user account with username, email, and password"
)
async def register_user(
    request: UserRegistrationRequest,
    use_case: RegisterUser = Depends(get_register_user_use_case)
) -> UserResponse:
    """Register a new user"""
    try:
        # Convert API schema to use case request
        use_case_request = RegisterUserRequest(
            username=request.username,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=request.password,
            avatar=request.avatar
        )
        
        # Execute use case
        response = await use_case.execute(use_case_request)
        
        # Convert use case response to API schema
        return UserResponse(
            user_id=response.user_id,
            username=response.username,
            email=response.email,
            first_name=response.first_name,
            last_name=response.last_name,
            is_active=response.is_active,
            credits=response.credits,
            avatar=response.avatar
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account deactivated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="User login",
    description="Authenticate user and return JWT access token (OAuth2 compatible)"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    use_case: AuthenticateUser = Depends(get_authenticate_user_use_case)
) -> TokenResponse:
    """Login user and return JWT token (OAuth2 compatible endpoint)"""
    try:
        # Convert OAuth2 form data to use case request
        use_case_request = AuthenticateUserRequest(
            username_or_email=form_data.username,
            password=form_data.password
        )
        
        # Execute use case
        response = await use_case.execute(use_case_request)
        
        # Convert use case response to API schema
        return TokenResponse(
            access_token=response.access_token,
            token_type=response.token_type,
            expires_in=response.expires_in,
            user_id=response.user_id,
            username=response.username,
            email=response.email
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserNotActiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during authentication"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        403: {"model": ErrorResponse, "description": "Account deactivated"}
    },
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user profile"""
    return UserResponse(
        user_id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        credits=current_user.credits,
        avatar=current_user.avatar
    )