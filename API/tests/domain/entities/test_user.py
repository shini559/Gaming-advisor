from datetime import datetime, timezone
from uuid import uuid4
import pytest

from app.domain.entities.user import User


class TestUser:
  """Tests pour l'entité User"""

  def test_user_create_with_valid_data(self) -> None:
      """Test création utilisateur avec données valides"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="hashed_password_123",
          token_credits=100
      )

      assert user.id is not None
      assert user.username == "testuser"
      assert user.email == "test@example.com"
      assert user.first_name == "Test"
      assert user.last_name == "User"
      assert user.hashed_password == "hashed_password_123"
      assert user.is_active is True
      assert user.is_subscribed is False
      assert user.token_credits == 100
      assert user.created_at is not None
      assert user.updated_at is not None

  def test_user_create_strips_and_lowercases_inputs(self) -> None:
      """Test normalisation des entrées (strip + lowercase)"""
      user = User.create(
          username="  TestUser  ",
          email="  TEST@EXAMPLE.COM  ",
          first_name="  Test  ",
          last_name="  User  ",
          hashed_password="password"
      )

      assert user.username == "testuser"
      assert user.email == "test@example.com"
      assert user.first_name == "Test"
      assert user.last_name == "User"

  def test_user_full_name_property(self) -> None:
      """Test propriété full_name"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="John",
          last_name="Doe",
          hashed_password="password"
      )

      assert user.full_name == "John Doe"

  def test_user_activate_deactivate(self) -> None:
      """Test activation/désactivation utilisateur"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password"
      )

      # Test désactivation
      original_updated_at = user.updated_at
      user.deactivate()
      assert user.is_active is False
      assert user.updated_at != original_updated_at

      # Test réactivation
      updated_at_after_deactivate = user.updated_at
      user.activate()
      assert user.is_active is True
      assert user.updated_at != updated_at_after_deactivate

  def test_user_default_values(self) -> None:
      """Test valeurs par défaut lors de la création"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password"
      )

      assert user.token_credits == 0
      assert user.avatar is None
      assert user.is_active is True
      assert user.is_subscribed is False