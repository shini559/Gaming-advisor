from datetime import datetime, timezone
from uuid import uuid4
import pytest

from app.domain.entities.user import User


class TestUser:
  """Tests pour l'entité User"""

  def test_user_create_with_valid_data(self):
      """Test création utilisateur avec données valides"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="hashed_password_123",
          credits=100
      )

      assert user.id is not None
      assert user.username == "testuser"
      assert user.email == "test@example.com"
      assert user.first_name == "Test"
      assert user.last_name == "User"
      assert user.hashed_password == "hashed_password_123"
      assert user.is_active is True
      assert user.is_subscribed is False
      assert user.credits == 100
      assert user.created_at is not None
      assert user.updated_at is not None

  def test_user_create_strips_and_lowercases_inputs(self):
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

  def test_user_full_name_property(self):
      """Test propriété full_name"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="John",
          last_name="Doe",
          hashed_password="password"
      )

      assert user.full_name == "John Doe"

  def test_user_activate_deactivate(self):
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

  def test_user_subscribe_unsubscribe(self):
      """Test souscription/désouscription"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password"
      )

      # Test souscription
      original_updated_at = user.updated_at
      user.subscribe()
      assert user.is_subscribed is True
      assert user.updated_at != original_updated_at

      # Test désouscription
      updated_at_after_subscribe = user.updated_at
      user.unsubscribe()
      assert user.is_subscribed is False
      assert user.updated_at != updated_at_after_subscribe

  def test_add_credits_valid_amount(self):
      """Test ajout de crédits avec montant valide"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password",
          credits=10
      )

      original_updated_at = user.updated_at
      user.add_credits(50)

      assert user.credits == 60
      assert user.updated_at != original_updated_at

  def test_add_credits_invalid_amount(self):
      """Test ajout de crédits avec montant invalide"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password"
      )

      with pytest.raises(ValueError, match="Cannot add negative credits"):
          user.add_credits(-10)

      with pytest.raises(ValueError, match="Cannot add negative credits"):
          user.add_credits(0)

  def test_consume_credits_successful(self):
      """Test consommation de crédits réussie"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password",
          credits=100
      )

      original_updated_at = user.updated_at
      result = user.consume_credits(30)

      assert result is True
      assert user.credits == 70
      assert user.updated_at != original_updated_at

  def test_consume_credits_insufficient_balance(self):
      """Test consommation de crédits insuffisants"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password",
          credits=10
      )

      original_updated_at = user.updated_at
      result = user.consume_credits(50)

      assert result is True
      assert user.credits == 0
      assert user.updated_at != original_updated_at

  def test_consume_credits_invalid_amount(self):
      """Test consommation de crédits avec montant invalide"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password"
      )

      with pytest.raises(ValueError, match="No credits available"):
          user.consume_credits(-10)

      with pytest.raises(ValueError, match="No credits available"):
          user.consume_credits(0)

  def test_user_default_values(self):
      """Test valeurs par défaut lors de la création"""
      user = User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="password"
      )

      assert user.credits == 0
      assert user.avatar is None
      assert user.is_active is True
      assert user.is_subscribed is False