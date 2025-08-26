from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.domain.ports.repositories.user_repository import IUserRepository
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository

from app.domain.ports.services.jwt_service import IJWTService
from app.domain.ports.services.password_service import IPasswordService


@dataclass
class AuthenticateUserRequest:
    """Request DTO pour l'authentification utilisateur"""
    username_or_email: str
    password: str
    device_info: Optional[Dict[str, Any]] = None

@dataclass
class AuthenticateUserResponse:
    """Response DTO pour l'authentification utilisateur"""
    access_token: str
    refresh_token: str
    token_type: str
    user_id: str
    username: str
    email: str
    expires_in: int
    refresh_expires_in: int

class InvalidCredentialsError(Exception):
    """Levée quand les identifiants utilisateur sont invalides"""
    pass


class UserNotActiveError(Exception):
    """Levée quand le compte utilisateur n'est pas actif"""
    pass


class AuthenticateUser:
    """Use case pour l'authentification utilisateur"""

    def __init__(
            self,
            user_repository: IUserRepository,
            session_repository: IUserSessionRepository,
            password_service: IPasswordService,
            jwt_service: IJWTService
    ):
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def execute(self, request: AuthenticateUserRequest) -> AuthenticateUserResponse:
        """Exécuter l'authentification utilisateur"""

        # Valider l'entrée
        self._validate_request(request)

        # Trouver l'utilisateur par email ou nom d'utilisateur
        user = await self._find_user(request.username_or_email)
        if not user:
            raise InvalidCredentialsError("Invalid username/email or password")

        # Vérifier si l'utilisateur est actif
        if not user.is_active:
            raise UserNotActiveError("User account is deactivated")

        # Vérifier le mot de passe
        if not self._password_service.verify_password(request.password, user.hashed_password):
            raise InvalidCredentialsError("Invalid username/email or password")

        # Générer les tokens JWT
        access_token, refresh_token, refresh_token_hash, access_expires_in, refresh_expires_in = \
            self._jwt_service.create_token_pair(user.id, user.username, user.email)

        # Créer une nouvelle session
        session = UserSession.create(
            user_id=user.id,
            refresh_token_hash=refresh_token_hash,
            expires_at=self._jwt_service.get_refresh_token_expiry(),
            device_info=request.device_info
        )

        # Sauvegarder la session
        await self._session_repository.save(session)

        # Nettoyer les anciennes sessions expirées (optionnel, en arrière-plan)
        try:
            await self._session_repository.cleanup_expired_sessions()
        except Exception:
            # Ne pas faire échouer l'authentification si le nettoyage échoue
            pass

        # Retourner la réponse
        return AuthenticateUserResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in
        )

    async def _find_user(self, username_or_email: str) -> Optional[User]:
        """Trouver un utilisateur par nom d'utilisateur ou email"""
        # Essayer de trouver par email d'abord
        if "@" in username_or_email:
            user = await self._user_repository.find_by_email(username_or_email)
            if user:
                return user

        # Essayer de trouver par nom d'utilisateur
        return await self._user_repository.find_by_username(username_or_email)

    def _validate_request(self, request: AuthenticateUserRequest) -> None:
        """Valider la requête d'authentification"""
        errors = []

        if not request.username_or_email or len(request.username_or_email.strip()) == 0:
            errors.append("Username or email is required")

        if not request.password or len(request.password) == 0:
            errors.append("Password is required")

        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")