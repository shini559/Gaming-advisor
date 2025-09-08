from dataclasses import dataclass
from typing import Optional, Any, Dict

from app.domain.ports.repositories.user_repository import IUserRepository
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository
from app.domain.ports.services.jwt_service import IJWTService


@dataclass
class RefreshTokenRequest:
  """Request DTO pour le rafraîchissement du token"""
  refresh_token: str
  device_info: Optional[Dict[str, Any]] = None


@dataclass
class RefreshTokenResponse:
  """Response DTO pour le rafraîchissement du token"""
  access_token: str
  refresh_token: str
  token_type: str
  expires_in: int
  refresh_expires_in: int
  user_id: str
  username: str
  email: str


class InvalidRefreshTokenError(Exception):
  """Levée quand le refresh token est invalide"""
  pass


class ExpiredRefreshTokenError(Exception):
  """Levée quand le refresh token est expiré"""
  pass


class RefreshToken:
  """Use case pour le rafraîchissement des tokens"""

  def __init__(
      self,
      user_repository: IUserRepository,
      session_repository: IUserSessionRepository,
      jwt_service: IJWTService
  ):
      self._user_repository = user_repository
      self._session_repository = session_repository
      self._jwt_service = jwt_service

  async def execute(self, request: RefreshTokenRequest) -> RefreshTokenResponse:
      """Exécuter le rafraîchissement du token"""

      # Valider la requête
      self._validate_request(request)

      # Hasher le refresh token pour la recherche
      token_hash = self._jwt_service.hash_refresh_token(request.refresh_token)

      # Trouver la session correspondante
      session = await self._session_repository.find_by_refresh_token_hash(token_hash)
      if not session:
          raise InvalidRefreshTokenError("Invalid refresh token")

      # Vérifier que la session est valide
      if not session.is_valid():
          # Nettoyer la session expirée/inactive
          await self._session_repository.deactivate_session(session.id)

          if session.is_expired():
              raise ExpiredRefreshTokenError("Refresh token has expired")
          else:
              raise InvalidRefreshTokenError("Session is no longer active")

      # Vérifier le refresh token
      if not self._jwt_service.verify_refresh_token(request.refresh_token, session.refresh_token_hash):
          raise InvalidRefreshTokenError("Invalid refresh token")

      # Récupérer l'utilisateur
      user = await self._user_repository.find_by_id(session.user_id)
      if not user:
          raise InvalidRefreshTokenError("User not found")

      if not user.is_active:
          raise InvalidRefreshTokenError("User account is deactivated")

      # Générer de nouveaux tokens (rotation du refresh token)
      access_token, new_refresh_token, new_refresh_hash, access_expires_in, refresh_expires_in = \
          self._jwt_service.create_token_pair(user.id, user.username, user.email)

      # Mettre à jour la session avec le nouveau refresh token
      session.refresh_token_hash = new_refresh_hash
      session.update_last_used()
      if request.device_info:
          if not session.device_info:
              session.device_info = {}
          session.device_info.update(request.device_info)

      # Sauvegarder la session mise à jour
      await self._session_repository.save(session)

      # Retourner la réponse
      return RefreshTokenResponse(
          access_token=access_token,
          refresh_token=new_refresh_token,
          token_type="bearer",
          expires_in=access_expires_in,
          refresh_expires_in=refresh_expires_in,
          user_id=str(user.id),
          username=user.username,
          email=user.email
      )

  def _validate_request(self, request: RefreshTokenRequest) -> None:
      """Valider la requête de rafraîchissement"""
      errors = []

      if not request.refresh_token or len(request.refresh_token.strip()) == 0:
          errors.append("Refresh token is required")

      if errors:
          raise ValueError(f"Validation errors: {', '.join(errors)}")