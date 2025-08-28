import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta

from app.data.repositories.user_session_repository import UserSessionRepository
from app.domain.entities.user_session import UserSession
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository


class TestUserSessionRepository:
  """Tests pour le repository UserSessionRepository"""

  @pytest_asyncio.fixture
  async def repository(self, db_session) -> IUserSessionRepository:
      """Fixture pour créer une instance du repository avec session DB"""
      return UserSessionRepository(db_session)

  @pytest.fixture
  def user_id(self) -> UUID:
      """Fixture pour un ID utilisateur de test"""
      return uuid4()

  @pytest.fixture
  def another_user_id(self) -> UUID:
      """Fixture pour un autre ID utilisateur de test"""
      return uuid4()

  @pytest.fixture
  def test_session(self, user_id: UUID) -> UserSession:
      """Fixture pour créer une session de test"""
      return UserSession.create(
          user_id=user_id,
          refresh_token_hash="test_hash_123",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7),
          device_info={"platform": "web", "user_agent": "Chrome"}
      )

  @pytest.fixture
  def expired_session(self, user_id: UUID) -> UserSession:
      """Fixture pour créer une session expirée"""
      return UserSession.create(
          user_id=user_id,
          refresh_token_hash="expired_hash_456",
          expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
          device_info={"platform": "mobile"}
      )

  @pytest.mark.asyncio
  async def test_save_new_session(self, repository: IUserSessionRepository, test_session: UserSession) -> None:
      """Test sauvegarde d'une nouvelle session"""
      # Execute
      saved_session = await repository.save(test_session)

      # Assert
      assert saved_session.id == test_session.id
      assert saved_session.user_id == test_session.user_id
      assert saved_session.refresh_token_hash == "test_hash_123"
      assert saved_session.device_info == {"platform": "web", "user_agent": "Chrome"}
      assert saved_session.is_active is True
      assert saved_session.created_at is not None
      assert saved_session.last_used_at is not None

  @pytest.mark.asyncio
  async def test_save_update_existing_session(self, repository: IUserSessionRepository, test_session: UserSession) -> None:
      """Test mise à jour d'une session existante"""
      # Save session first
      saved_session = await repository.save(test_session)

      # Modify session
      saved_session.refresh_token_hash = "new_hash_789"
      saved_session.device_info = {"platform": "desktop"}
      saved_session.is_active = False
      saved_session.last_used_at = datetime.now(timezone.utc)

      # Update session
      updated_session = await repository.save(saved_session)

      # Assert
      assert updated_session.id == saved_session.id
      assert updated_session.refresh_token_hash == "new_hash_789"
      assert updated_session.device_info == {"platform": "desktop"}
      assert updated_session.is_active is False

      # Verify it's the same session (not a new one)
      found_session = await repository.find_by_id(saved_session.id)
      assert found_session.refresh_token_hash == "new_hash_789"

  @pytest.mark.asyncio
  async def test_find_by_id_existing_session(self, repository: IUserSessionRepository, test_session: UserSession) -> None:
      """Test recherche par ID d'une session existante"""
      # Save session first
      saved_session = await repository.save(test_session)

      # Find session by ID
      found_session = await repository.find_by_id(saved_session.id)

      # Assert
      assert found_session is not None
      assert found_session.id == saved_session.id
      assert found_session.user_id == saved_session.user_id
      assert found_session.refresh_token_hash == saved_session.refresh_token_hash

  @pytest.mark.asyncio
  async def test_find_by_id_non_existing_session(self, repository: IUserSessionRepository) -> None:
      """Test recherche par ID d'une session inexistante"""
      non_existing_id = uuid4()

      # Find session by non-existing ID
      found_session = await repository.find_by_id(non_existing_id)

      # Assert
      assert found_session is None

  @pytest.mark.asyncio
  async def test_find_by_refresh_token_hash_existing(self, repository: IUserSessionRepository, test_session: UserSession) -> None:
      """Test recherche par hash de refresh token existant"""
      # Save session first
      await repository.save(test_session)

      # Find session by token hash
      found_session = await repository.find_by_refresh_token_hash("test_hash_123")

      # Assert
      assert found_session is not None
      assert found_session.refresh_token_hash == "test_hash_123"
      assert found_session.user_id == test_session.user_id

  @pytest.mark.asyncio
  async def test_find_by_refresh_token_hash_non_existing(self, repository: IUserSessionRepository) -> None:
      """Test recherche par hash de refresh token inexistant"""
      found_session = await repository.find_by_refresh_token_hash("non_existing_hash")
      assert found_session is None

  @pytest.mark.asyncio
  async def test_find_active_by_user_id_with_active_sessions(self, repository: IUserSessionRepository, user_id: UUID) -> None:
      """Test recherche des sessions actives d'un utilisateur"""
      # Create multiple sessions for user
      session1 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="hash1",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7),
          device_info={"platform": "web"}
      )
      session2 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="hash2",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7),
          device_info={"platform": "mobile"}
      )
      # Inactive session
      session3 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="hash3",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7),
          device_info={"platform": "desktop"}
      )
      session3.is_active = False

      # Save all sessions
      await repository.save(session1)
      await repository.save(session2)
      await repository.save(session3)

      # Find active sessions
      active_sessions = await repository.find_active_by_user_id(user_id)

      # Assert - should return only active sessions
      assert len(active_sessions) == 2
      session_hashes = [s.refresh_token_hash for s in active_sessions]
      assert "hash1" in session_hashes
      assert "hash2" in session_hashes
      assert "hash3" not in session_hashes  # Inactive session excluded

  @pytest.mark.asyncio
  async def test_find_active_by_user_id_excludes_expired(self, repository: IUserSessionRepository, user_id: UUID, expired_session: UserSession) -> None:
      """Test que find_active_by_user_id exclut les sessions expirées"""
      # Save expired session
      await repository.save(expired_session)

      # Find active sessions
      active_sessions = await repository.find_active_by_user_id(user_id)

      # Assert - expired session should not be returned
      assert len(active_sessions) == 0

  @pytest.mark.asyncio
  async def test_find_active_by_user_id_different_users(self, repository: IUserSessionRepository, user_id: UUID, another_user_id: UUID) -> None:
      """Test que find_active_by_user_id ne retourne que les sessions du bon utilisateur"""
      # Create sessions for different users
      session_user1 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="user1_hash",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )
      session_user2 = UserSession.create(
          user_id=another_user_id,
          refresh_token_hash="user2_hash",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )

      # Save both sessions
      await repository.save(session_user1)
      await repository.save(session_user2)

      # Find sessions for user1
      user1_sessions = await repository.find_active_by_user_id(user_id)
      user2_sessions = await repository.find_active_by_user_id(another_user_id)

      # Assert - each user should only see their own sessions
      assert len(user1_sessions) == 1
      assert len(user2_sessions) == 1
      assert user1_sessions[0].refresh_token_hash == "user1_hash"
      assert user2_sessions[0].refresh_token_hash == "user2_hash"

  @pytest.mark.asyncio
  async def test_deactivate_session_existing(self, repository: IUserSessionRepository, test_session: UserSession) -> None:
      """Test désactivation d'une session existante"""
      # Save session first
      saved_session = await repository.save(test_session)
      assert saved_session.is_active is True

      # Deactivate session
      result = await repository.deactivate_session(saved_session.id)

      # Assert
      assert result is True

      # Verify session is deactivated
      found_session = await repository.find_by_id(saved_session.id)
      assert found_session.is_active is False

  @pytest.mark.asyncio
  async def test_deactivate_session_non_existing(self, repository: IUserSessionRepository) -> None:
      """Test désactivation d'une session inexistante"""
      non_existing_id = uuid4()

      # Try to deactivate non-existing session
      result = await repository.deactivate_session(non_existing_id)

      # Assert
      assert result is False

  @pytest.mark.asyncio
  async def test_deactivate_all_user_sessions(self, repository: IUserSessionRepository, user_id: UUID, another_user_id) -> None:
      """Test désactivation de toutes les sessions d'un utilisateur"""
      # Create multiple sessions for user1 and user2
      session1_user1 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="user1_hash1",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )
      session2_user1 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="user1_hash2",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )
      session1_user2 = UserSession.create(
          user_id=another_user_id,
          refresh_token_hash="user2_hash1",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )

      # Save all sessions
      await repository.save(session1_user1)
      await repository.save(session2_user1)
      await repository.save(session1_user2)

      # Deactivate all sessions for user1
      count = await repository.deactivate_all_user_sessions(user_id)

      # Assert
      assert count == 2  # 2 sessions deactivated for user1

      # Verify user1 sessions are deactivated
      user1_sessions = await repository.find_active_by_user_id(user_id)
      assert len(user1_sessions) == 0

      # Verify user2 sessions are still active
      user2_sessions = await repository.find_active_by_user_id(another_user_id)
      assert len(user2_sessions) == 1

  @pytest.mark.asyncio
  async def test_deactivate_all_user_sessions_no_active_sessions(self, repository: IUserSessionRepository, user_id: UUID) -> None:
      """Test désactivation de toutes les sessions quand aucune session active"""
      # Deactivate all sessions for user (no sessions exist)
      count = await repository.deactivate_all_user_sessions(user_id)

      # Assert
      assert count == 0

  @pytest.mark.asyncio
  async def test_cleanup_expired_sessions(self, repository, user_id) -> None:
      """Test nettoyage des sessions expirées"""
      # Create expired and active sessions
      expired_session = UserSession.create(
          user_id=user_id,
          refresh_token_hash="expired_hash",
          expires_at=datetime.now(timezone.utc) - timedelta(days=1)  # Expired
      )
      active_session = UserSession.create(
          user_id=user_id,
          refresh_token_hash="active_hash",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # Active
      )

      # Save both sessions
      await repository.save(expired_session)
      await repository.save(active_session)

      # Cleanup expired sessions
      count = await repository.cleanup_expired_sessions()

      # Assert
      assert count == 1  # 1 expired session cleaned up

      # Verify expired session is deleted
      found_expired = await repository.find_by_id(expired_session.id)
      assert found_expired is None

      # Verify active session still exists
      found_active = await repository.find_by_id(active_session.id)
      assert found_active is not None

  @pytest.mark.asyncio
  async def test_cleanup_expired_sessions_none_expired(self, repository: IUserSessionRepository, user_id: UUID) -> None:
      """Test nettoyage quand aucune session expirée"""
      # Create only active session
      active_session = UserSession.create(
          user_id=user_id,
          refresh_token_hash="active_hash",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )
      await repository.save(active_session)

      # Cleanup expired sessions
      count = await repository.cleanup_expired_sessions()

      # Assert
      assert count == 0  # No sessions to clean up

  @pytest.mark.asyncio
  async def test_count_active_sessions_for_user(self, repository: IUserSessionRepository, user_id: UUID, another_user_id: UUID) -> None:
      """Test comptage des sessions actives pour un utilisateur"""
      # Create sessions for user1
      session1 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="hash1",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )
      session2 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="hash2",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )
      # Inactive session
      session3 = UserSession.create(
          user_id=user_id,
          refresh_token_hash="hash3",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )
      session3.is_active = False

      # Session for another user
      session_user2 = UserSession.create(
          user_id=another_user_id,
          refresh_token_hash="user2_hash",
          expires_at=datetime.now(timezone.utc) + timedelta(days=7)
      )

      # Save all sessions
      await repository.save(session1)
      await repository.save(session2)
      await repository.save(session3)
      await repository.save(session_user2)

      # Count active sessions
      count_user1 = await repository.count_active_sessions_for_user(user_id)
      count_user2 = await repository.count_active_sessions_for_user(another_user_id)

      # Assert
      assert count_user1 == 2  # 2 active sessions for user1
      assert count_user2 == 1  # 1 active session for user2

  @pytest.mark.asyncio
  async def test_count_active_sessions_excludes_expired(self, repository: IUserSessionRepository, user_id: UUID) -> None:
      """Test que le comptage exclut les sessions expirées"""
      # Create expired session
      expired_session = UserSession.create(
          user_id=user_id,
          refresh_token_hash="expired_hash",
          expires_at=datetime.now(timezone.utc) - timedelta(days=1)
      )
      await repository.save(expired_session)

      # Count active sessions
      count = await repository.count_active_sessions_for_user(user_id)

      # Assert
      assert count == 0  # Expired session not counted

  @pytest.mark.asyncio
  async def test_domain_model_conversion_roundtrip(self, repository: IUserSessionRepository, test_session: UserSession) -> None:
      """Test conversion domain ↔ model fonctionne correctement"""
      # Save session (domain → model → domain)
      saved_session = await repository.save(test_session)

      # Assert all fields preserved
      assert saved_session.id == test_session.id
      assert saved_session.user_id == test_session.user_id
      assert saved_session.refresh_token_hash == test_session.refresh_token_hash
      assert saved_session.device_info == test_session.device_info
      assert saved_session.is_active == test_session.is_active
      # Dates should be preserved (within reasonable tolerance)
      assert abs((saved_session.expires_at - test_session.expires_at).total_seconds()) < 1
      assert abs((saved_session.created_at - test_session.created_at).total_seconds()) < 1
      assert abs((saved_session.last_used_at - test_session.last_used_at).total_seconds()) < 1