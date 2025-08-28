from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.ports.services.jwt_service import IJWTService
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository


@dataclass
class LogoutUserRequest:
    """Request DTO pour la déconnexion utilisateur"""
    refresh_token: Optional[str] = None
    session_id: Optional[UUID] = None
    logout_all: bool = False


@dataclass
class LogoutUserResponse:
    """Response DTO pour la déconnexion utilisateur"""
    success: bool
    sessions_revoked: int
    message: str


class LogoutUser:
    """Use case pour la déconnexion utilisateur"""

    def __init__(
            self,
            session_repository: IUserSessionRepository,
            jwt_service: IJWTService
    ):
        self._session_repository = session_repository
        self._jwt_service = jwt_service

    async def execute(self, request: LogoutUserRequest, current_user_id: UUID) -> LogoutUserResponse:
        """Exécuter la déconnexion utilisateur"""

        # Valider la requête
        self._validate_request(request)

        if request.logout_all:
            # Déconnecter toutes les sessions de l'utilisateur
            sessions_revoked = await self._session_repository.deactivate_all_user_sessions(current_user_id)
            return LogoutUserResponse(
                success=True,
                sessions_revoked=sessions_revoked,
                message=f"Successfully logged out from {sessions_revoked} sessions"
            )

        elif request.session_id:
            # Déconnecter une session spécifique par ID
            # Vérifier que la session appartient à l'utilisateur courant
            session = await self._session_repository.find_by_id(request.session_id)
            if not session or session.user_id != current_user_id:
                return LogoutUserResponse(
                    success=False,
                    sessions_revoked=0,
                    message="Session not found or access denied"
                )

            success = await self._session_repository.deactivate_session(request.session_id)
            return LogoutUserResponse(
                success=success,
                sessions_revoked=1 if success else 0,
                message="Successfully logged out" if success else "Failed to logout"
            )

        elif request.refresh_token:
            # Déconnecter la session correspondant au refresh token
            token_hash = self._jwt_service.hash_refresh_token(request.refresh_token)
            session = await self._session_repository.find_by_refresh_token_hash(token_hash)

            if not session or session.user_id != current_user_id:
                return LogoutUserResponse(
                    success=False,
                    sessions_revoked=0,
                    message="Invalid refresh token or access denied"
                )

            success = await self._session_repository.deactivate_session(session.id)
            return LogoutUserResponse(
                success=success,
                sessions_revoked=1 if success else 0,
                message="Successfully logged out" if success else "Failed to logout"
            )

        else:
            return LogoutUserResponse(
                success=False,
                sessions_revoked=0,
                message="No logout method specified"
            )

    def _validate_request(self, request: LogoutUserRequest) -> None:
        """Valider la requête de déconnexion"""
        if not request.logout_all and not request.session_id and not request.refresh_token:
            raise ValueError("Must specify either logout_all=True, session_id, or refresh_token")