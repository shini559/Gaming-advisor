from datetime import timezone, datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models.user_session import UserSessionModel
from app.domain.entities.user_session import UserSession
from app.domain.ports.repositories.user_session_repository import IUserSessionRepository


class UserSessionRepository(IUserSessionRepository):
    """Implémentation du repository pour les sessions utilisateur"""

    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session

    async def save(self, session: UserSession) -> UserSession:
        """Sauvegarder une session"""
        # Vérifier si la session existe déjà
        existing_session = await self._db_session.get(UserSessionModel, session.id)

        if existing_session:
            # Mettre à jour la session existante
            existing_session.refresh_token_hash = session.refresh_token_hash
            existing_session.device_info = session.device_info
            existing_session.expires_at = session.expires_at
            existing_session.last_used_at = session.last_used_at
            existing_session.is_active = session.is_active
            db_session = existing_session
        else:
            # Créer une nouvelle session
            db_session = UserSessionModel(
                id=session.id,
                user_id=session.user_id,
                refresh_token_hash=session.refresh_token_hash,
                device_info=session.device_info,
                expires_at=session.expires_at,
                created_at=session.created_at,
                last_used_at=session.last_used_at,
                is_active=session.is_active
            )
            self._db_session.add(db_session)

        await self._db_session.commit()
        await self._db_session.refresh(db_session)

        return self._to_entity(db_session)

    async def find_by_id(self, session_id: UUID) -> Optional[UserSession]:
        """Trouver une session par son ID"""
        db_session = await self._db_session.get(UserSessionModel, session_id)
        return self._to_entity(db_session) if db_session else None

    async def find_by_refresh_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Trouver une session par le hash du refresh token"""

        try:
            print(f"🔍 Searching for token hash: {token_hash[:20]}...")
            stmt = select(UserSessionModel).where(
                UserSessionModel.refresh_token_hash == token_hash
            )
            result = await self._db_session.execute(stmt)
            db_session = result.scalar_one_or_none()
            print(f"📋 DB result: {db_session is not None}")

            if db_session:
                entity = self._to_entity(db_session)
                print(f"✅ Entity created: {entity.id}")
                return entity
            return None

        except Exception as e:
            print(f"🔴 Repository error: {type(e).__name__}: {str(e)}")
            raise

    async def find_active_by_user_id(self, user_id: UUID) -> List[UserSession]:
        """Trouver toutes les sessions actives d'un utilisateur"""

        stmt = select(UserSessionModel).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.is_active == True,
            UserSessionModel.expires_at > datetime.now(timezone.utc)
        ).order_by(UserSessionModel.last_used_at.desc())

        result = await self._db_session.execute(stmt)
        db_sessions = result.scalars().all()

        return [self._to_entity(db_session) for db_session in db_sessions]

    async def deactivate_session(self, session_id: UUID) -> bool:
        """Désactiver une session spécifique"""
        stmt = update(UserSessionModel).where(
            UserSessionModel.id == session_id
        ).values(is_active=False)

        result = await self._db_session.execute(stmt)
        await self._db_session.commit()

        return result.rowcount > 0

    async def deactivate_all_user_sessions(self, user_id: UUID) -> int:
        """Désactiver toutes les sessions d'un utilisateur"""
        stmt = update(UserSessionModel).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.is_active == True
        ).values(is_active=False)

        result = await self._db_session.execute(stmt)
        await self._db_session.commit()

        return result.rowcount

    async def cleanup_expired_sessions(self) -> int:
        """Nettoyer les sessions expirées"""
        now = datetime.now(timezone.utc)
        stmt = delete(UserSessionModel).where(
            UserSessionModel.expires_at < now
        )

        result = await self._db_session.execute(stmt)
        await self._db_session.commit()

        return result.rowcount

    async def count_active_sessions_for_user(self, user_id: UUID) -> int:
        """Compter les sessions actives d'un utilisateur"""
        now = datetime.now(timezone.utc)
        stmt = select(func.count(UserSessionModel.id)).where(
            UserSessionModel.user_id == user_id,
            UserSessionModel.is_active == True,
            UserSessionModel.expires_at > now
        )

        result = await self._db_session.execute(stmt)
        return result.scalar() or 0

    def _to_entity(self, db_session: UserSessionModel) -> UserSession:
        """Convertir le modèle en entité"""
        return UserSession(
            id=db_session.id,
            user_id=db_session.user_id,
            refresh_token_hash=db_session.refresh_token_hash,
            device_info=db_session.device_info,
            expires_at=db_session.expires_at,
            created_at=db_session.created_at,
            last_used_at=db_session.last_used_at,
            is_active=db_session.is_active
        )