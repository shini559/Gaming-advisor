import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone

from app.data.repositories.user_repository import UserRepository
from app.domain.entities.user import User


class TestUserRepository:
  """Tests pour le repository UserRepository"""

  @pytest_asyncio.fixture
  async def repository(self, db_session) -> UserRepository:
      """Fixture pour créer une instance du repository avec session DB"""
      return UserRepository(db_session)

  @pytest.fixture
  def test_user(self) -> User:
      """Fixture pour créer un utilisateur de test"""
      return User.create(
          username="testuser",
          email="test@example.com",
          first_name="Test",
          last_name="User",
          hashed_password="hashed_password_123",
          token_credits=100
      )

  @pytest.fixture
  def another_user(self) -> User:
      """Fixture pour créer un second utilisateur de test"""
      return User.create(
          username="anotheruser",
          email="another@example.com",
          first_name="Another",
          last_name="User",
          hashed_password="hashed_password_456",
          token_credits=50
      )

  @pytest.mark.asyncio
  async def test_save_new_user(self, repository: UserRepository, test_user: User) -> None:
      """Test sauvegarde d'un nouvel utilisateur"""
      # Execute
      saved_user = await repository.save(test_user)

      # Assert
      assert saved_user.id == test_user.id
      assert saved_user.username == "testuser"
      assert saved_user.email == "test@example.com"
      assert saved_user.first_name == "Test"
      assert saved_user.last_name == "User"
      assert saved_user.hashed_password == "hashed_password_123"
      assert saved_user.is_active is True
      assert saved_user.is_subscribed is False
      assert saved_user.token_credits == 100
      assert saved_user.created_at is not None
      assert saved_user.updated_at is not None

  @pytest.mark.asyncio
  async def test_save_duplicate_email_fails(self, repository: UserRepository, test_user: User) -> None:
      """Test sauvegarde avec email en double échoue"""
      # Save first user
      await repository.save(test_user)

      # Try to save user with same email
      duplicate_user = User.create(
          username="differentuser",
          email="test@example.com",  # Same email
          first_name="Different",
          last_name="User",
          hashed_password="different_password"
      )

      with pytest.raises(ValueError, match="User with this email or username already exists"):
          await repository.save(duplicate_user)

  @pytest.mark.asyncio
  async def test_save_duplicate_username_fails(self, repository: UserRepository, test_user: User) -> None:
      """Test sauvegarde avec username en double échoue"""
      # Save first user
      await repository.save(test_user)

      # Try to save user with same username
      duplicate_user = User.create(
          username="testuser",  # Same username
          email="different@example.com",
          first_name="Different",
          last_name="User",
          hashed_password="different_password"
      )

      with pytest.raises(ValueError, match="User with this email or username already exists"):
          await repository.save(duplicate_user)

  @pytest.mark.asyncio
  async def test_update_existing_user(self, repository: UserRepository, test_user: User) -> None:
      """Test mise à jour d'un utilisateur existant"""
      # Save user first
      saved_user = await repository.save(test_user)

      # Modify user
      saved_user.first_name = "Modified"
      saved_user.token_credits = 200
      saved_user.is_subscribed = True
      saved_user.updated_at = datetime.now(timezone.utc)

      # Update user
      updated_user = await repository.save(saved_user)

      # Assert
      assert updated_user.id == saved_user.id
      assert updated_user.first_name == "Modified"
      assert updated_user.token_credits == 200
      assert updated_user.is_subscribed is True
      # Verify it's the same user (not a new one)
      found_user = await repository.find_by_id(saved_user.id)
      assert found_user.first_name == "Modified"

  @pytest.mark.asyncio
  async def test_find_by_id_existing_user(self, repository: UserRepository, test_user: User) -> None:
      """Test recherche par ID d'un utilisateur existant"""
      # Save user first
      saved_user = await repository.save(test_user)

      # Find user by ID
      found_user = await repository.find_by_id(saved_user.id)

      # Assert
      assert found_user is not None
      assert found_user.id == saved_user.id
      assert found_user.username == saved_user.username
      assert found_user.email == saved_user.email

  @pytest.mark.asyncio
  async def test_find_by_id_non_existing_user(self, repository: UserRepository) -> None:
      """Test recherche par ID d'un utilisateur inexistant"""
      non_existing_id = uuid4()

      # Find user by non-existing ID
      found_user = await repository.find_by_id(non_existing_id)

      # Assert
      assert found_user is None

  @pytest.mark.asyncio
  async def test_find_by_email_existing_user(self, repository: UserRepository, test_user: User) -> None:
      """Test recherche par email d'un utilisateur existant"""
      # Save user first
      await repository.save(test_user)

      # Find user by email
      found_user = await repository.find_by_email("test@example.com")

      # Assert
      assert found_user is not None
      assert found_user.email == "test@example.com"
      assert found_user.username == "testuser"

  @pytest.mark.asyncio
  async def test_find_by_email_case_insensitive(self, repository: UserRepository, test_user: User) -> None:
      """Test recherche par email insensible à la casse"""
      # Save user first
      await repository.save(test_user)

      # Find user by email with different case
      found_user = await repository.find_by_email("TEST@EXAMPLE.COM")

      # Assert
      assert found_user is not None
      assert found_user.email == "test@example.com"

  @pytest.mark.asyncio
  async def test_find_by_email_non_existing(self, repository: UserRepository) -> None:
      """Test recherche par email inexistant"""
      found_user = await repository.find_by_email("nonexistent@example.com")
      assert found_user is None

  @pytest.mark.asyncio
  async def test_find_by_username_existing_user(self, repository: UserRepository, test_user: User) -> None:
      """Test recherche par username d'un utilisateur existant"""
      # Save user first
      await repository.save(test_user)

      # Find user by username
      found_user = await repository.find_by_username("testuser")

      # Assert
      assert found_user is not None
      assert found_user.username == "testuser"
      assert found_user.email == "test@example.com"

  @pytest.mark.asyncio
  async def test_find_by_username_case_insensitive(self, repository: UserRepository, test_user: User) -> None:
      """Test recherche par username insensible à la casse"""
      # Save user first
      await repository.save(test_user)

      # Find user by username with different case
      found_user = await repository.find_by_username("TESTUSER")

      # Assert
      assert found_user is not None
      assert found_user.username == "testuser"

  @pytest.mark.asyncio
  async def test_find_by_username_non_existing(self, repository: UserRepository) -> None:
      """Test recherche par username inexistant"""
      found_user = await repository.find_by_username("nonexistent")
      assert found_user is None

  @pytest.mark.asyncio
  async def test_exists_by_email_true(self, repository: UserRepository, test_user: User) -> None:
      """Test exists_by_email retourne True pour email existant"""
      # Save user first
      await repository.save(test_user)

      # Check if user exists by email
      exists = await repository.exists_by_email("test@example.com")

      # Assert
      assert exists is True

  @pytest.mark.asyncio
  async def test_exists_by_email_case_insensitive(self, repository: UserRepository, test_user: User) -> None:
      """Test exists_by_email insensible à la casse"""
      # Save user first
      await repository.save(test_user)

      # Check if user exists by email with different case
      exists = await repository.exists_by_email("TEST@EXAMPLE.COM")

      # Assert
      assert exists is True

  @pytest.mark.asyncio
  async def test_exists_by_email_false(self, repository: UserRepository) -> None:
      """Test exists_by_email retourne False pour email inexistant"""
      exists = await repository.exists_by_email("nonexistent@example.com")
      assert exists is False

  @pytest.mark.asyncio
  async def test_exists_by_username_true(self, repository: UserRepository, test_user: User) -> None:
      """Test exists_by_username retourne True pour username existant"""
      # Save user first
      await repository.save(test_user)

      # Check if user exists by username
      exists = await repository.exists_by_username("testuser")

      # Assert
      assert exists is True

  @pytest.mark.asyncio
  async def test_exists_by_username_case_insensitive(self, repository: UserRepository, test_user: User) -> None:
      """Test exists_by_username insensible à la casse"""
      # Save user first
      await repository.save(test_user)

      # Check if user exists by username with different case
      exists = await repository.exists_by_username("TESTUSER")

      # Assert
      assert exists is True

  @pytest.mark.asyncio
  async def test_exists_by_username_false(self, repository: UserRepository) -> None:
      """Test exists_by_username retourne False pour username inexistant"""
      exists = await repository.exists_by_username("nonexistent")
      assert exists is False

  @pytest.mark.asyncio
  async def test_delete_existing_user(self, repository: UserRepository, test_user: User):
      """Test suppression d'un utilisateur existant"""
      # Save user first
      saved_user = await repository.save(test_user)

      # Delete user
      deleted = await repository.delete(saved_user.id)

      # Assert
      assert deleted is True

      # Verify user no longer exists
      found_user = await repository.find_by_id(saved_user.id)
      assert found_user is None

  @pytest.mark.asyncio
  async def test_delete_non_existing_user(self, repository: UserRepository) -> None:
      """Test suppression d'un utilisateur inexistant"""
      non_existing_id = uuid4()

      # Try to delete non-existing user
      deleted = await repository.delete(non_existing_id)

      # Assert
      assert deleted is False

  @pytest.mark.asyncio
  async def test_multiple_users_independent(self, repository: UserRepository, test_user: User, another_user: User) -> None:
      """Test que plusieurs utilisateurs sont indépendants"""
      # Save both users
      saved_user1 = await repository.save(test_user)
      saved_user2 = await repository.save(another_user)

      # Verify both exist independently
      found_user1 = await repository.find_by_id(saved_user1.id)
      found_user2 = await repository.find_by_id(saved_user2.id)

      assert found_user1 is not None
      assert found_user2 is not None
      assert found_user1.id != found_user2.id
      assert found_user1.email != found_user2.email
      assert found_user1.username != found_user2.username

  @pytest.mark.asyncio
  async def test_domain_model_conversion_roundtrip(self, repository: UserRepository, test_user: User) -> None:
      """Test conversion domain ↔ model fonctionne correctement"""
      # Save user (domain → model → domain)
      saved_user = await repository.save(test_user)

      # Assert all fields preserved
      assert saved_user.id == test_user.id
      assert saved_user.username == test_user.username
      assert saved_user.email == test_user.email
      assert saved_user.first_name == test_user.first_name
      assert saved_user.last_name == test_user.last_name
      assert saved_user.avatar == test_user.avatar
      assert saved_user.hashed_password == test_user.hashed_password
      assert saved_user.is_active == test_user.is_active
      assert saved_user.is_subscribed == test_user.is_subscribed
      assert saved_user.token_credits == test_user.token_credits
      # Dates should be preserved (within reasonable tolerance)
      assert abs((saved_user.created_at - test_user.created_at).total_seconds()) < 1
      assert abs((saved_user.updated_at - test_user.updated_at).total_seconds()) < 1