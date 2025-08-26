from unittest.mock import AsyncMock, Mock
from uuid import uuid4
import pytest

from app.domain.use_cases.auth.logout_user import (
  LogoutUser,
  LogoutUserRequest,
  LogoutUserResponse
)
from app.domain.entities.user_session import UserSession
from datetime import datetime, timezone


class TestLogoutUser:
  """Tests pour le use case LogoutUser"""

  @pytest.fixture
  def mock_dependencies(self):
      return {
          "session_repository": AsyncMock(),
          "jwt_service": AsyncMock()
      }

  @pytest.fixture
  def use_case(self, mock_dependencies):
      return LogoutUser(**mock_dependencies)

  @pytest.fixture
  def current_user_id(self):
      return uuid4()

  @pytest.fixture
  def test_session(self, current_user_id):
      return UserSession.create(
          user_id=current_user_id,
          refresh_token_hash="test_hash",
          expires_at=datetime.now(timezone.utc),
          device_info={"platform": "web"}
      )

  @pytest.mark.asyncio
  async def test_logout_all_sessions_successful(self, use_case, mock_dependencies, current_user_id):
      """Test déconnexion de toutes les sessions"""
      request = LogoutUserRequest(logout_all=True)
      mock_dependencies["session_repository"].deactivate_all_user_sessions.return_value = 3

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert isinstance(result, LogoutUserResponse)
      assert result.success is True
      assert result.sessions_revoked == 3
      assert "Successfully logged out from 3 sessions" in result.message
      mock_dependencies["session_repository"].deactivate_all_user_sessions.assert_called_once_with(current_user_id)

  @pytest.mark.asyncio
  async def test_logout_all_sessions_no_sessions(self, use_case, mock_dependencies, current_user_id):
      """Test déconnexion de toutes les sessions quand aucune session active"""
      request = LogoutUserRequest(logout_all=True)
      mock_dependencies["session_repository"].deactivate_all_user_sessions.return_value = 0

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is True
      assert result.sessions_revoked == 0
      assert "Successfully logged out from 0 sessions" in result.message

  @pytest.mark.asyncio
  async def test_logout_by_session_id_successful(self, use_case, mock_dependencies, current_user_id, test_session):
      """Test déconnexion par session ID réussie"""
      request = LogoutUserRequest(session_id=test_session.id)
      mock_dependencies["session_repository"].find_by_id.return_value = test_session
      mock_dependencies["session_repository"].deactivate_session.return_value = True

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is True
      assert result.sessions_revoked == 1
      assert result.message == "Successfully logged out"
      mock_dependencies["session_repository"].find_by_id.assert_called_once_with(test_session.id)
      mock_dependencies["session_repository"].deactivate_session.assert_called_once_with(test_session.id)

  @pytest.mark.asyncio
  async def test_logout_by_session_id_not_found(self, use_case, mock_dependencies, current_user_id):
      """Test déconnexion par session ID non trouvée"""
      session_id = uuid4()
      request = LogoutUserRequest(session_id=session_id)
      mock_dependencies["session_repository"].find_by_id.return_value = None

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is False
      assert result.sessions_revoked == 0
      assert result.message == "Session not found or access denied"

  @pytest.mark.asyncio
  async def test_logout_by_session_id_wrong_user(self, use_case, mock_dependencies, current_user_id, test_session):
      """Test déconnexion par session ID appartenant à un autre utilisateur"""
      other_user_id = uuid4()
      test_session.user_id = other_user_id  # Session d'un autre utilisateur
      request = LogoutUserRequest(session_id=test_session.id)
      mock_dependencies["session_repository"].find_by_id.return_value = test_session

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is False
      assert result.sessions_revoked == 0
      assert result.message == "Session not found or access denied"
      # Should not try to deactivate
      mock_dependencies["session_repository"].deactivate_session.assert_not_called()

  @pytest.mark.asyncio
  async def test_logout_by_session_id_deactivation_failed(self, use_case, mock_dependencies, current_user_id, test_session):
      """Test déconnexion par session ID avec échec de désactivation"""
      request = LogoutUserRequest(session_id=test_session.id)
      mock_dependencies["session_repository"].find_by_id.return_value = test_session
      mock_dependencies["session_repository"].deactivate_session.return_value = False

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is False
      assert result.sessions_revoked == 0
      assert result.message == "Failed to logout"

  @pytest.mark.asyncio
  async def test_logout_by_refresh_token_successful(self, use_case, mock_dependencies, current_user_id, test_session):
      """Test déconnexion par refresh token réussie"""
      refresh_token = "valid_refresh_token"
      token_hash = "hashed_token"
      request = LogoutUserRequest(refresh_token=refresh_token)

      mock_dependencies["jwt_service"].hash_refresh_token = Mock(return_value=token_hash)
      mock_dependencies["session_repository"].find_by_refresh_token_hash.return_value = test_session
      mock_dependencies["session_repository"].deactivate_session.return_value = True

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is True
      assert result.sessions_revoked == 1
      assert result.message == "Successfully logged out"
      mock_dependencies["jwt_service"].hash_refresh_token.assert_called_once_with(refresh_token)
      mock_dependencies["session_repository"].find_by_refresh_token_hash.assert_called_once_with(token_hash)
      mock_dependencies["session_repository"].deactivate_session.assert_called_once_with(test_session.id)

  @pytest.mark.asyncio
  async def test_logout_by_refresh_token_not_found(self, use_case, mock_dependencies, current_user_id):
      """Test déconnexion par refresh token non trouvé"""
      refresh_token = "invalid_refresh_token"
      token_hash = "hashed_token"
      request = LogoutUserRequest(refresh_token=refresh_token)

      mock_dependencies["jwt_service"]._hash_refresh_token = Mock(return_value=token_hash)
      mock_dependencies["session_repository"].find_by_refresh_token_hash.return_value = None

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is False
      assert result.sessions_revoked == 0
      assert result.message == "Invalid refresh token or access denied"

  @pytest.mark.asyncio
  async def test_logout_by_refresh_token_wrong_user(self, use_case, mock_dependencies, current_user_id, test_session):
      """Test déconnexion par refresh token appartenant à un autre utilisateur"""
      other_user_id = uuid4()
      test_session.user_id = other_user_id
      refresh_token = "valid_refresh_token"
      token_hash = "hashed_token"
      request = LogoutUserRequest(refresh_token=refresh_token)

      mock_dependencies["jwt_service"]._hash_refresh_token = Mock(return_value=token_hash)
      mock_dependencies["session_repository"].find_by_refresh_token_hash.return_value = test_session

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is False
      assert result.sessions_revoked == 0
      assert result.message == "Invalid refresh token or access denied"
      mock_dependencies["session_repository"].deactivate_session.assert_not_called()

  @pytest.mark.asyncio
  async def test_logout_by_refresh_token_deactivation_failed(self, use_case, mock_dependencies, current_user_id, test_session):
      """Test déconnexion par refresh token avec échec de désactivation"""
      refresh_token = "valid_refresh_token"
      token_hash = "hashed_token"
      request = LogoutUserRequest(refresh_token=refresh_token)

      mock_dependencies["jwt_service"]._hash_refresh_token = Mock(return_value=token_hash)
      mock_dependencies["session_repository"].find_by_refresh_token_hash.return_value = test_session
      mock_dependencies["session_repository"].deactivate_session.return_value = False

      # Execute
      result = await use_case.execute(request, current_user_id)

      # Assert
      assert result.success is False
      assert result.sessions_revoked == 0
      assert result.message == "Failed to logout"

  @pytest.mark.asyncio
  async def test_logout_no_method_specified(self, use_case, mock_dependencies, current_user_id):
      """Test déconnexion sans méthode spécifiée"""
      request = LogoutUserRequest()  # Aucune méthode

      # Execute & Assert
      with pytest.raises(ValueError, match="Must specify either logout_all=True, session_id, or refresh_token"):
          await use_case.execute(request, current_user_id)

  def test_validation_no_method_specified(self, use_case):
      """Test validation sans méthode spécifiée"""
      request = LogoutUserRequest()

      with pytest.raises(ValueError, match="Must specify either logout_all=True, session_id, or refresh_token"):
          use_case._validate_request(request)

  def test_validation_logout_all_true(self, use_case):
      """Test validation avec logout_all=True (valide)"""
      request = LogoutUserRequest(logout_all=True)

      # Should not raise
      use_case._validate_request(request)

  def test_validation_with_session_id(self, use_case):
      """Test validation avec session_id (valide)"""
      request = LogoutUserRequest(session_id=uuid4())

      # Should not raise
      use_case._validate_request(request)

  def test_validation_with_refresh_token(self, use_case):
      """Test validation avec refresh_token (valide)"""
      request = LogoutUserRequest(refresh_token="token")

      # Should not raise
      use_case._validate_request(request)

  def test_validation_multiple_methods_allowed(self, use_case):
      """Test validation avec plusieurs méthodes (permis)"""
      request = LogoutUserRequest(
          logout_all=True,
          session_id=uuid4(),
          refresh_token="token"
      )

      # Should not raise - multiple methods are allowed, logout_all takes precedence
      use_case._validate_request(request)