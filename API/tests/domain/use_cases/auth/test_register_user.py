from typing import Coroutine, Any
from unittest.mock import AsyncMock
import pytest

from app.domain.use_cases.auth.register_user import RegisterUser, RegisterUserRequest, UserAlreadyExistsError


class TestRegisterUser:
  @pytest.fixture
  def mock_dependencies(self) -> dict:
      return {
          "user_repository": AsyncMock(),
          "password_service": AsyncMock()
      }

  @pytest.fixture
  def use_case(self, mock_dependencies) -> RegisterUser:
      return RegisterUser(**mock_dependencies)

  @pytest.fixture
  def valid_request(self) -> RegisterUserRequest:
      return RegisterUserRequest(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          password="password123"
      )

  @pytest.mark.asyncio
  async def test_successful_registration(self, use_case, mock_dependencies, valid_request) -> None:
      """Test inscription réussie"""
      # Setup mocks
      mock_dependencies["user_repository"].exists_by_username.return_value = False
      mock_dependencies["user_repository"].exists_by_email.return_value = False
      mock_dependencies["password_service"].hash_password.return_value = "hashed_password"

      # Execute
      result = await use_case.execute(valid_request)

      # Assert
      assert result.user_id is not None
      mock_dependencies["user_repository"].save.assert_called_once()

  @pytest.mark.asyncio
  async def test_username_already_exists(self, use_case, mock_dependencies, valid_request) -> None:
      """Test username déjà existant"""
      mock_dependencies["user_repository"].exists_by_username.return_value = True

      with pytest.raises(UserAlreadyExistsError):
          await use_case.execute(valid_request)

  @pytest.mark.asyncio
  async def test_email_already_exists(self, use_case, mock_dependencies, valid_request) -> None:
      """Test email déjà existant"""
      mock_dependencies["user_repository"].exists_by_username.return_value = False
      mock_dependencies["user_repository"].exists_by_email.return_value = True

      with pytest.raises(UserAlreadyExistsError):
          await use_case.execute(valid_request)