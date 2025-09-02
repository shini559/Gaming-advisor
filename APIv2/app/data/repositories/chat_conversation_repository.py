from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models.chat_conversation import ChatConversationModel
from app.domain.entities.chat_conversation import ChatConversation
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository


class ChatConversationRepository(IChatConversationRepository):
    """Implémentation concrète du repository pour les conversations de chat"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, conversation: ChatConversation) -> ChatConversation:
        """Créer une nouvelle conversation"""
        model = ChatConversationModel(
            id=conversation.id,
            game_id=conversation.game_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)
    
    async def get_by_id(self, conversation_id: UUID) -> Optional[ChatConversation]:
        """Récupérer une conversation par son ID"""
        stmt = select(ChatConversationModel).where(
            ChatConversationModel.id == conversation_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_by_user_id(self, user_id: UUID, limit: int = 20, offset: int = 0) -> List[ChatConversation]:
        """Récupérer les conversations d'un utilisateur avec pagination"""
        stmt = select(ChatConversationModel).where(
            ChatConversationModel.user_id == user_id
        ).order_by(
            ChatConversationModel.updated_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_by_game_id(self, game_id: UUID, limit: int = 50, offset: int = 0) -> List[ChatConversation]:
        """Récupérer les conversations d'un jeu avec pagination"""
        stmt = select(ChatConversationModel).where(
            ChatConversationModel.game_id == game_id
        ).order_by(
            ChatConversationModel.updated_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def get_by_game_and_user(
        self, 
        game_id: UUID, 
        user_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[ChatConversation]:
        """Récupérer les conversations d'un utilisateur pour un jeu spécifique"""
        stmt = select(ChatConversationModel).where(
            ChatConversationModel.user_id == user_id,
            ChatConversationModel.game_id == game_id
        ).order_by(
            ChatConversationModel.updated_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def update(self, conversation: ChatConversation) -> ChatConversation:
        """Mettre à jour une conversation"""
        stmt = select(ChatConversationModel).where(
            ChatConversationModel.id == conversation.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.title = conversation.title
            model.updated_at = conversation.updated_at
            await self._session.flush()
            return self._model_to_entity(model)
        
        raise ValueError("Conversation not found for update")
    
    async def delete(self, conversation_id: UUID) -> bool:
        """Supprimer une conversation"""
        stmt = select(ChatConversationModel).where(
            ChatConversationModel.id == conversation_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            await self._session.delete(model)
            return True
        return False
    
    async def exists_for_user(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Vérifier qu'une conversation appartient à un utilisateur"""
        stmt = select(func.count()).select_from(ChatConversationModel).where(
            ChatConversationModel.id == conversation_id,
            ChatConversationModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def count_by_user_id(self, user_id: UUID) -> int:
        """Compter les conversations d'un utilisateur"""
        stmt = select(func.count()).select_from(ChatConversationModel).where(
            ChatConversationModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar()
    
    async def count_by_game_and_user(self, game_id: UUID, user_id: UUID) -> int:
        """Compter les conversations d'un utilisateur pour un jeu spécifique"""
        stmt = select(func.count()).select_from(ChatConversationModel).where(
            ChatConversationModel.game_id == game_id,
            ChatConversationModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar()
    
    async def count_by_game(self, game_id: UUID) -> int:
        """Compter les conversations d'un jeu"""
        stmt = select(func.count()).select_from(ChatConversationModel).where(
            ChatConversationModel.game_id == game_id
        )
        result = await self._session.execute(stmt)
        return result.scalar()
    
    async def delete_by_user_id(self, user_id: UUID) -> int:
        """Supprimer toutes les conversations d'un utilisateur"""
        stmt = delete(ChatConversationModel).where(
            ChatConversationModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount
    
    def _model_to_entity(self, model: ChatConversationModel) -> ChatConversation:
        """Convertit un modèle en entité"""
        return ChatConversation(
            id=model.id,
            game_id=model.game_id,
            user_id=model.user_id,
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at
        )