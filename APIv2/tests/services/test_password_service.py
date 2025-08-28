import pytest

from app.domain.ports.services.password_service import IPasswordService
from app.services.password_service import PasswordService


class TestPasswordService:
  @pytest.fixture
  def password_service(self) -> IPasswordService:
      return PasswordService()

  def test_hash_password(self, password_service: IPasswordService) -> None:
      """Test hachage password"""
      password = "test_password_123"
      hashed = password_service.hash_password(password)

      assert hashed != password
      assert len(hashed) > 50  # bcrypt hash length
      assert hashed.startswith("$2b$")

  def test_verify_password_correct(self, password_service: IPasswordService) -> None:
      """Test vérification password correct"""
      password = "test_password_123"
      hashed = password_service.hash_password(password)

      result = password_service.verify_password(password, hashed)
      assert result is True

  def test_verify_password_incorrect(self, password_service: IPasswordService) -> None:
      """Test vérification password incorrect"""
      password = "test_password_123"
      wrong_password = "wrong_password"
      hashed = password_service.hash_password(password)

      result = password_service.verify_password(wrong_password, hashed)
      assert result is False

  def test_needs_rehash(self, password_service: IPasswordService) -> None:
      """Test besoin de re-hash"""
      password = "test_password_123"
      hashed = password_service.hash_password(password)

      # Un hash bcrypt récent ne devrait pas avoir besoin d'être re-hashé
      result = password_service.needs_update(hashed)
      assert result is False