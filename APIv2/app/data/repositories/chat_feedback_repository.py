from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.data.models.chat_feedback import ChatFeedbackModel
from app.data.models.chat_message import ChatMessageModel
from app.domain.entities.chat_feedback import ChatFeedback, FeedbackType
from app.domain.ports.repositories.chat_feedback_repository import IChatFeedbackRepository


class ChatFeedbackRepository(IChatFeedbackRepository):
    """Implémentation concrète du repository pour les feedbacks de messages"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, feedback: ChatFeedback) -> ChatFeedback:
        """Créer un nouveau feedback"""
        model = ChatFeedbackModel(
            id=feedback.id,
            message_id=feedback.message_id,
            user_id=feedback.user_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at
        )
        
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)
    
    async def get_by_id(self, feedback_id: UUID) -> Optional[ChatFeedback]:
        """Récupérer un feedback par son ID"""
        stmt = select(ChatFeedbackModel).where(
            ChatFeedbackModel.id == feedback_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_by_message_id(self, message_id: UUID) -> Optional[ChatFeedback]:
        """Récupérer le feedback d'un message (un seul feedback par message)"""
        stmt = select(ChatFeedbackModel).where(
            ChatFeedbackModel.message_id == message_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_by_message_and_user(self, message_id: UUID, user_id: UUID) -> Optional[ChatFeedback]:
        """Récupérer le feedback d'un message pour un utilisateur spécifique"""
        stmt = select(ChatFeedbackModel).where(
            and_(
                ChatFeedbackModel.message_id == message_id,
                ChatFeedbackModel.user_id == user_id
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_by_conversation_id(self, conversation_id: UUID) -> List[ChatFeedback]:
        """Récupérer tous les feedbacks d'une conversation"""
        stmt = select(ChatFeedbackModel).join(
            ChatMessageModel,
            ChatFeedbackModel.message_id == ChatMessageModel.id
        ).where(
            ChatMessageModel.conversation_id == conversation_id
        ).order_by(
            ChatFeedbackModel.created_at.desc()
        )
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def update(self, feedback: ChatFeedback) -> ChatFeedback:
        """Mettre à jour un feedback existant"""
        stmt = select(ChatFeedbackModel).where(
            ChatFeedbackModel.id == feedback.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.feedback_type = feedback.feedback_type
            model.comment = feedback.comment
            model.updated_at = feedback.updated_at
            await self._session.flush()
            return self._model_to_entity(model)
        
        raise ValueError("Feedback not found for update")
    
    async def delete(self, feedback_id: UUID) -> bool:
        """Supprimer un feedback"""
        stmt = select(ChatFeedbackModel).where(
            ChatFeedbackModel.id == feedback_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            await self._session.delete(model)
            return True
        return False
    
    async def exists_for_message(self, message_id: UUID) -> bool:
        """Vérifier si un message a déjà un feedback"""
        stmt = select(func.count()).select_from(ChatFeedbackModel).where(
            ChatFeedbackModel.message_id == message_id
        )
        result = await self._session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def get_positive_feedback_count(self, conversation_id: UUID) -> int:
        """Compter les feedbacks positifs d'une conversation"""
        stmt = select(func.count()).select_from(
            ChatFeedbackModel
        ).join(
            ChatMessageModel,
            ChatFeedbackModel.message_id == ChatMessageModel.id
        ).where(
            and_(
                ChatMessageModel.conversation_id == conversation_id,
                ChatFeedbackModel.feedback_type == FeedbackType.POSITIVE
            )
        )
        
        result = await self._session.execute(stmt)
        return result.scalar()
    
    async def get_negative_feedback_count(self, conversation_id: UUID) -> int:
        """Compter les feedbacks négatifs d'une conversation"""
        stmt = select(func.count()).select_from(
            ChatFeedbackModel
        ).join(
            ChatMessageModel,
            ChatFeedbackModel.message_id == ChatMessageModel.id
        ).where(
            and_(
                ChatMessageModel.conversation_id == conversation_id,
                ChatFeedbackModel.feedback_type == FeedbackType.NEGATIVE
            )
        )
        
        result = await self._session.execute(stmt)
        return result.scalar()
    
    def _model_to_entity(self, model: ChatFeedbackModel) -> ChatFeedback:
        """Convertit un modèle en entité"""
        return ChatFeedback(
            id=model.id,
            message_id=model.message_id,
            user_id=model.user_id,
            feedback_type=model.feedback_type,
            comment=model.comment,
            created_at=model.created_at,
            updated_at=model.updated_at
        )