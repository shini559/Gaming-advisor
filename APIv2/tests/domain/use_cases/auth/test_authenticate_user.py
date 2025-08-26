from unittest.mock import AsyncMock, Mock

from app.config import settings
import pytest

from app.domain.use_cases.auth.authenticate_user import (
  AuthenticateUser,
  AuthenticateUserRequest,
  AuthenticateUserResponse,
  InvalidCredentialsError,
  UserNotActiveError
)
from app.domain.entities.user import User
from datetime import datetime, timezone


class TestAuthenticateUser:
  """Tests pour le use case AuthenticateUser"""

  @pytest.fixture
  def mock_dependencies(self):
      return {
          "user_repository": AsyncMock(),
          "session_repository": AsyncMock(),
          "password_service": AsyncMock(),
          "jwt_service": AsyncMock()
      }

  @pytest.fixture
  def use_case(self, mock_dependencies):
      return AuthenticateUser(**mock_dependencies)

  @pytest.fixture
  def use_case_for_validation(self):
      """Use case avec mocks simples pour les tests de validation uniquement"""
      return AuthenticateUser(
          user_repository=Mock(),
          session_repository=Mock(),
          password_service=Mock(),
          jwt_service=Mock()
      )

  @pytest.fixture
  def test_user(self):
      return User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="hashed_password_123"
      )

  @pytest.fixture
  def valid_request_email(self):
      return AuthenticateUserRequest(
          username_or_email="test@example.com",
          password="password123",
          device_info={"platform": "web", "user_agent": "Chrome"}
      )

  @pytest.fixture
  def valid_request_username(self):
      return AuthenticateUserRequest(
          username_or_email="testuser",
          password="password123"
      )

  @pytest.mark.asyncio
  async def test_successful_authentication_with_email(self, use_case, mock_dependencies, valid_request_email, test_user):
      """Test authentification réussie avec email"""
      # Setup mocks
      mock_dependencies["user_repository"].find_by_email.return_value = test_user
      mock_dependencies["password_service"].verify_password = Mock(return_value=True)
      mock_dependencies["jwt_service"].create_token_pair = Mock(return_value=(
          "access_token", "refresh_token", "refresh_hash",
          settings.jwt_access_token_expire_minutes * 60,
          settings.jwt_refresh_token_expire_days * 24 * 60 * 60
      ))
      mock_dependencies["jwt_service"].get_refresh_token_expiry = Mock(return_value=datetime.now(timezone.utc))

      # Execute
      result = await use_case.execute(valid_request_email)

      # Assert
      assert isinstance(result, AuthenticateUserResponse)
      assert result.access_token == "access_token"
      assert result.refresh_token == "refresh_token"
      assert result.token_type == "bearer"
      assert result.user_id == str(test_user.id)
      assert result.username == test_user.username
      assert result.email == test_user.email
      assert result.expires_in == settings.jwt_access_token_expire_minutes * 60
      assert result.refresh_expires_in == settings.jwt_refresh_token_expire_days * 24 * 60 * 60

      # Verify session was saved
      mock_dependencies["session_repository"].save.assert_called_once()

  @pytest.mark.asyncio
  async def test_successful_authentication_with_username(self, use_case, mock_dependencies, valid_request_username, test_user):
      """Test authentification réussie avec username"""
      # Setup mocks
      mock_dependencies["user_repository"].find_by_email.return_value = None
      mock_dependencies["user_repository"].find_by_username.return_value = test_user
      mock_dependencies["password_service"].verify_password = Mock(return_value=True)
      mock_dependencies["jwt_service"].create_token_pair = Mock(return_value=(
          "access_token", "refresh_token", "refresh_hash",
          settings.jwt_access_token_expire_minutes * 60,
          settings.jwt_refresh_token_expire_days * 24 * 60 * 60
      ))
      mock_dependencies["jwt_service"].get_refresh_token_expiry = Mock(return_value=datetime.now(timezone.utc))

      # Execute
      result = await use_case.execute(valid_request_username)

      # Assert
      assert result.access_token == "access_token"
      mock_dependencies["user_repository"].find_by_username.assert_called_once_with("testuser")

  @pytest.mark.asyncio
  async def test_authentication_user_not_found(self, use_case, mock_dependencies, valid_request_email):
      """Test authentification avec utilisateur non trouvé"""
      # Setup mocks
      mock_dependencies["user_repository"].find_by_email.return_value = None
      mock_dependencies["user_repository"].find_by_username.return_value = None
      mock_dependencies["password_service"].verify_password = Mock()

      # Execute & Assert
      with pytest.raises(InvalidCredentialsError, match="Invalid username/email or password"):
          await use_case.execute(valid_request_email)

  @pytest.mark.asyncio
  async def test_authentication_user_inactive(self, use_case, mock_dependencies, valid_request_email, test_user):
      """Test authentification avec utilisateur inactif"""
      # Setup inactive user
      test_user.is_active = False
      mock_dependencies["user_repository"].find_by_email.return_value = test_user

      # Execute & Assert
      with pytest.raises(UserNotActiveError, match="User account is deactivated"):
          await use_case.execute(valid_request_email)

  @pytest.mark.asyncio
  async def test_authentication_invalid_password(self, use_case, mock_dependencies, valid_request_email, test_user):
      """Test authentification avec mot de passe invalide"""
      # Setup mocks
      mock_dependencies["user_repository"].find_by_email.return_value = test_user
      mock_dependencies["password_service"].verify_password = Mock(return_value=False)

      # Execute & Assert
      with pytest.raises(InvalidCredentialsError, match="Invalid username/email or password"):
          await use_case.execute(valid_request_email)

      # Verify password was checked
      mock_dependencies["password_service"].verify_password.assert_called_once_with(
          "password123", test_user.hashed_password
      )

  @pytest.mark.asyncio
  async def test_authentication_with_device_info(self, use_case, mock_dependencies, test_user):
      """Test authentification avec device_info"""
      device_info = {"platform": "mobile", "version": "1.0.0"}
      request = AuthenticateUserRequest(
          username_or_email="test@example.com",
          password="password123",
          device_info=device_info
      )

      # Setup mocks
      mock_dependencies["user_repository"].find_by_email.return_value = test_user
      mock_dependencies["password_service"].verify_password = Mock(return_value=True)
      mock_dependencies["jwt_service"].create_token_pair = Mock(return_value=(
          "access_token", "refresh_token", "refresh_hash",
          settings.jwt_access_token_expire_minutes * 60,
          settings.jwt_refresh_token_expire_days * 24 * 60 * 60
      ))
      mock_dependencies["jwt_service"].get_refresh_token_expiry = Mock(return_value=datetime.now(timezone.utc))

      # Execute
      await use_case.execute(request)

      # Verify session was created with device_info
      save_call = mock_dependencies["session_repository"].save.call_args[0][0]
      assert save_call.device_info == device_info

  @pytest.mark.asyncio
  async def test_session_cleanup_failure_does_not_break_auth(self, use_case, mock_dependencies, valid_request_email, test_user):
      """Test que l'échec du nettoyage des sessions n'interrompt pas l'auth"""
      # Setup mocks
      mock_dependencies["user_repository"].find_by_email.return_value = test_user
      mock_dependencies["password_service"].verify_password = Mock(return_value=True)
      mock_dependencies["jwt_service"].create_token_pair = Mock(return_value=(
          "access_token", "refresh_token", "refresh_hash",
          settings.jwt_access_token_expire_minutes * 60,
          settings.jwt_refresh_token_expire_days * 24 * 60 * 60
      ))
      mock_dependencies["jwt_service"].get_refresh_token_expiry = Mock(return_value=datetime.now(timezone.utc))
      mock_dependencies["session_repository"].cleanup_expired_sessions.side_effect = Exception("Cleanup failed")

      # Execute - should not raise exception
      result = await use_case.execute(valid_request_email)

      # Assert - auth still succeeds
      assert result.access_token == "access_token"

  def test_validation_empty_username_or_email(self, use_case_for_validation):
      """Test validation avec username/email vide"""
      request = AuthenticateUserRequest(
          username_or_email="",
          password="password123",
      )

      with pytest.raises(ValueError, match="Username or email is required"):
          use_case_for_validation._validate_request(request)

  def test_validation_empty_password(self, use_case_for_validation):
      """Test validation avec password vide"""
      request = AuthenticateUserRequest(
          username_or_email="test@example.com",
          password=""
      )

      with pytest.raises(ValueError, match="Password is required"):
          use_case_for_validation._validate_request(request)

  def test_validation_multiple_errors(self, use_case_for_validation):
      """Test validation avec plusieurs erreurs"""
      request = AuthenticateUserRequest(
          username_or_email="",
          password=""
      )

      with pytest.raises(ValueError, match="Username or email is required.*Password is required"):
          use_case_for_validation._validate_request(request)

  @pytest.mark.asyncio
  async def test_find_user_prefers_email_over_username(self, use_case, mock_dependencies):
      """Test que find_user privilégie l'email quand @ est présent"""
      email_user = User.create("emailuser", "test@example.com", "Email", "User", "hash1")
      username_user = User.create("test@example.com", "other@example.com", "Username", "User", "hash2")

      mock_dependencies["user_repository"].find_by_email.return_value = email_user
      mock_dependencies["user_repository"].find_by_username.return_value = username_user

      result = await use_case._find_user("test@example.com")

      # Should return email user, not username user
      assert result == email_user
      mock_dependencies["user_repository"].find_by_email.assert_called_once_with("test@example.com")

  @pytest.mark.asyncio
  async def test_find_user_falls_back_to_username(self, use_case, mock_dependencies):
      """Test fallback vers username si email échoue"""
      username_user = User.create("test@example.com", "other@example.com", "Username", "User", "hash")

      mock_dependencies["user_repository"].find_by_email.return_value = None
      mock_dependencies["user_repository"].find_by_username.return_value = username_user

      result = await use_case._find_user("test@example.com")

      assert result == username_user
      mock_dependencies["user_repository"].find_by_username.assert_called_once_with("test@example.com")