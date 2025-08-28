from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models.chat_message import ChatMessageModel
from app.domain.entities.chat_message import ChatMessage, MessageRole, MessageSource
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository


class ChatMessageRepository(IChatMessageRepository):
    """Implémentation concrète du repository pour les messages de chat"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, message: ChatMessage) -> ChatMessage:
        """Créer un nouveau message"""
        # Sérialiser les sources en JSON
        sources_json = None
        if message.sources:
            sources_json = [
                {
                    "vector_id": str(source.vector_id),
                    "image_id": str(source.image_id) if source.image_id else None,
                    "similarity_score": source.similarity_score,
                    "content_snippet": source.content_snippet,
                    "image_url": source.image_url
                }
                for source in message.sources
            ]
        
        model = ChatMessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            sources=sources_json,
            created_at=message.created_at
        )
        
        self._session.add(model)
        await self._session.flush()
        return self._model_to_entity(model)
    
    async def get_by_id(self, message_id: UUID) -> Optional[ChatMessage]:
        """Récupérer un message par son ID"""
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.id == message_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_by_conversation_id(
        self, 
        conversation_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[ChatMessage]:
        """Récupérer les messages d'une conversation avec pagination"""
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.conversation_id == conversation_id
        ).order_by(
            ChatMessageModel.created_at.asc()
        ).limit(limit).offset(offset)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def count_by_conversation_id(self, conversation_id: UUID) -> int:
        """Compter les messages d'une conversation"""
        stmt = select(func.count()).select_from(ChatMessageModel).where(
            ChatMessageModel.conversation_id == conversation_id
        )
        result = await self._session.execute(stmt)
        return result.scalar()
    
    async def count_by_conversation(self, conversation_id: UUID) -> int:
        """Compter les messages d'une conversation (alias pour cohérence)"""
        return await self.count_by_conversation_id(conversation_id)
    
    async def get_conversation_history(
        self, 
        conversation_id: UUID, 
        limit_messages: int = 20,
        offset: int = 0
    ) -> List[ChatMessage]:
        """Récupérer les derniers messages d'une conversation pour le contexte IA"""
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.conversation_id == conversation_id
        ).order_by(
            ChatMessageModel.created_at.desc()
        ).limit(limit_messages).offset(offset)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        
        # Retourner dans l'ordre chronologique (plus ancien en premier)
        messages = [self._model_to_entity(model) for model in reversed(models)]
        return messages
    
    async def get_by_role(self, conversation_id: UUID, role: MessageRole) -> List[ChatMessage]:
        """Récupérer les messages d'un rôle spécifique dans une conversation"""
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.conversation_id == conversation_id,
            ChatMessageModel.role == role
        ).order_by(
            ChatMessageModel.created_at.asc()
        )
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def delete_by_conversation_id(self, conversation_id: UUID) -> int:
        """Supprimer tous les messages d'une conversation"""
        stmt = delete(ChatMessageModel).where(
            ChatMessageModel.conversation_id == conversation_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount
    
    async def update(self, message: ChatMessage) -> ChatMessage:
        """Mettre à jour un message (rarement utilisé)"""
        stmt = select(ChatMessageModel).where(
            ChatMessageModel.id == message.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.content = message.content
            
            # Mettre à jour les sources si présentes
            if message.sources:
                sources_json = [
                    {
                        "vector_id": str(source.vector_id),
                        "image_id": str(source.image_id) if source.image_id else None,
                        "similarity_score": source.similarity_score,
                        "content_snippet": source.content_snippet,
                        "image_url": source.image_url
                    }
                    for source in message.sources
                ]
                model.sources = sources_json
            else:
                model.sources = None
            
            await self._session.flush()
            return self._model_to_entity(model)
        
        raise ValueError("Message not found for update")
    
    def _model_to_entity(self, model: ChatMessageModel) -> ChatMessage:
        """Convertit un modèle en entité"""
        # Désérialiser les sources depuis JSON
        sources = []
        if model.sources:
            for source_data in model.sources:
                source = MessageSource(
                    vector_id=UUID(source_data["vector_id"]),
                    image_id=UUID(source_data["image_id"]) if source_data["image_id"] else None,
                    similarity_score=source_data["similarity_score"],
                    content_snippet=source_data["content_snippet"],
                    image_url=source_data.get("image_url")
                )
                sources.append(source)
        
        return ChatMessage(
            id=model.id,
            conversation_id=model.conversation_id,
            role=model.role,
            content=model.content,
            sources=sources,
            created_at=model.created_at
        )