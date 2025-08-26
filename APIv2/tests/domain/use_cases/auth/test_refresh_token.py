from datetime import timedelta, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.domain.use_cases.auth.refresh_token import RefreshToken, RefreshTokenRequest, InvalidRefreshTokenError, ExpiredRefreshTokenError


class TestRefreshTokenUseCase:
    @pytest.fixture
    def mock_dependencies(self):
        return {
            "user_repository": AsyncMock(),
            "session_repository": AsyncMock(),
            "jwt_service": MagicMock()
        }

    @pytest.fixture
    def use_case(self, mock_dependencies):
        return RefreshToken(**mock_dependencies)

    @pytest.fixture
    def valid_user(self):
        return User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hash",
            is_active=True,
            is_subscribed=False,
            credits=100,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.fixture
    def valid_session(self):
        return UserSession.create(
            user_id=uuid4(),
            refresh_token_hash="valid_hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=15)
        )

    @pytest.mark.asyncio
    async def test_successful_token_refresh(self, use_case, mock_dependencies, valid_user, valid_session):
        """Test refresh token réussi"""
        request = RefreshTokenRequest(refresh_token="valid_token")

        # Setup mocks
        mock_dependencies["jwt_service"]._hash_refresh_token.return_value = "valid_hash"
        mock_dependencies["session_repository"].find_by_refresh_token_hash.return_value = valid_session
        mock_dependencies["jwt_service"].verify_refresh_token.return_value = True
        mock_dependencies["user_repository"].find_by_id.return_value = valid_user
        mock_dependencies["jwt_service"].create_token_pair.return_value = (
            "new_access", "new_refresh", "new_hash", 3600, 2592000
        )

        result = await use_case.execute(request)

        # Vérifications
        assert result.access_token == "new_access"
        assert result.refresh_token == "new_refresh"
        assert result.user_id == str(valid_user.id)
        mock_dependencies["session_repository"].save.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_refresh_token_raises_error(self, use_case, mock_dependencies):
        """Test rejet d'un refresh token invalide"""
        request = RefreshTokenRequest(refresh_token="invalid_token")

        mock_dependencies["jwt_service"]._hash_refresh_token.return_value = "invalid_hash"
        mock_dependencies["session_repository"].find_by_refresh_token_hash.return_value = None

        with pytest.raises(InvalidRefreshTokenError):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_expired_session_raises_error(self, use_case, mock_dependencies):
        """Test rejet d'une session expirée"""
        expired_session = UserSession.create(
            user_id=uuid4(),
            refresh_token_hash="expired_hash",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )

        request = RefreshTokenRequest(refresh_token="expired_token")
        mock_dependencies["jwt_service"]._hash_refresh_token.return_value = "expired_hash"
        mock_dependencies["session_repository"].find_by_refresh_token_hash.return_value = expired_session

        with pytest.raises(ExpiredRefreshTokenError):
            await use_case.execute(request)