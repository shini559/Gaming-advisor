import time
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.domain.ports.services.jwt_service import IJWTService
from app.services.jwt_service import JWTService
from app.config import settings

@pytest.mark.ci_test
class TestJWTService:
    @pytest.fixture
    def jwt_service(self) -> IJWTService:
        return JWTService()

    @pytest.fixture
    def user_data(self) -> dict:
        return {
            "user_id": uuid4(),
            "username": "testuser",
            "email": "test@example.com"
        }

    def test_create_token_pair_returns_valid_tokens(self, jwt_service: IJWTService, user_data: dict) -> None:
        """Test génération d'une paire de tokens valide"""
        access_token, refresh_token, token_hash, access_exp, refresh_exp = jwt_service.create_token_pair(**user_data)

        # Vérifier que les tokens sont générés
        assert access_token is not None
        assert refresh_token is not None
        assert token_hash is not None

        # Vérifier les durées d'expiration
        assert access_exp == settings.jwt_access_token_expire_minutes * 60  # 4h en secondes
        assert refresh_exp == settings.jwt_refresh_token_expire_days * 24 * 60 * 60  # 30j en secondes

    def test_token_rotation_generates_different_tokens(self, jwt_service: IJWTService, user_data: dict) -> None:
        """Test que la rotation génère des tokens différents"""
        tokens1 = jwt_service.create_token_pair(**user_data)
        time.sleep(1)
        tokens2 = jwt_service.create_token_pair(**user_data)

        # Les tokens doivent être différents
        assert tokens1[0] != tokens2[0]  # access_token
        assert tokens1[1] != tokens2[1]  # refresh_token
        assert tokens1[2] != tokens2[2]  # token_hash

    def test_verify_valid_token(self, jwt_service: IJWTService, user_data: dict) -> None:
        """Test vérification d'un token valide"""
        access_token, _, _, _, _ = jwt_service.create_token_pair(**user_data)

        payload = jwt_service.verify_access_token(access_token)

        assert payload is not None
        assert payload["sub"] == str(user_data["user_id"])
        assert payload["username"] == user_data["username"]
        assert payload["type"] == "access_token"

    def test_verify_expired_token(self, jwt_service: IJWTService, user_data: dict) -> None:
        """Test rejet d'un token expiré"""
        with patch.object(jwt_service, '_access_token_expire_minutes', -1):
            access_token, _, _, _, _ = jwt_service.create_token_pair(**user_data)

        payload = jwt_service.verify_access_token(access_token)
        assert payload is None

    def test_verify_malformed_token(self, jwt_service: IJWTService) -> None:
        """Test rejet d'un token malformé"""
        payload = jwt_service.verify_access_token("invalid.token.here")
        assert payload is None

    def test_refresh_token_hash_consistency(self, jwt_service: IJWTService) -> None:
        """Test cohérence du hashing des refresh tokens"""
        token = "test_refresh_token"
        hash1 = jwt_service.hash_refresh_token(token)
        hash2 = jwt_service.hash_refresh_token(token)

        assert hash1 == hash2
        assert jwt_service.verify_refresh_token(token, hash1) is True
        assert jwt_service.verify_refresh_token("wrong_token", hash1) is False