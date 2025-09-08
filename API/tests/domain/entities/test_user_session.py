from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.domain.entities.user_session import UserSession


class TestUserSession:
    def test_create_session_with_valid_data(self) -> None:
        """Test création d'une session avec des données valides"""
        user_id = uuid4()
        token_hash = "hash123"
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        session = UserSession.create(
            user_id=user_id,
            refresh_token_hash=token_hash,
            expires_at=expires_at,
            device_info={"browser": "Chrome"}
        )

        assert session.user_id == user_id
        assert session.refresh_token_hash == token_hash
        assert session.is_active is True
        assert session.device_info == {"browser": "Chrome"}

    def test_session_expiration_logic(self) -> None:
        """Test logique d'expiration des sessions"""
        # Session expirée
        expired_session = UserSession.create(
            user_id=uuid4(),
            refresh_token_hash="hash",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        assert expired_session.is_expired() is True
        assert expired_session.is_valid() is False

        # Session valide
        valid_session = UserSession.create(
            user_id=uuid4(),
            refresh_token_hash="hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        assert valid_session.is_expired() is False
        assert valid_session.is_valid() is True

    def test_session_deactivation(self) -> None:
        """Test désactivation d'une session"""
        session = UserSession.create(
            user_id=uuid4(),
            refresh_token_hash="hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )

        session.deactivate()
        assert session.is_active is False
        assert session.is_valid() is False