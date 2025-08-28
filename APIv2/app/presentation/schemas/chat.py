from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.chat_feedback import FeedbackType
from app.domain.entities.chat_message import MessageRole


# Base schemas
class MessageSourceSchema(BaseModel):
    """Schema pour les sources d'un message assistant"""
    vector_id: UUID
    image_id: Optional[UUID] = None
    similarity_score: float
    content_snippet: str
    image_url: Optional[str] = None


class ChatMessageSchema(BaseModel):
    """Schema de base pour un message de chat"""
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    sources: Optional[List[MessageSourceSchema]] = None
    created_at: datetime

    class Config:
        use_enum_values = True


class ChatConversationSchema(BaseModel):
    """Schema de base pour une conversation de chat"""
    id: UUID
    game_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatFeedbackSchema(BaseModel):
    """Schema de base pour un feedback de message"""
    id: UUID
    message_id: UUID
    user_id: UUID
    feedback_type: FeedbackType
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True


# Request schemas
class CreateConversationRequest(BaseModel):
    """Request pour créer une nouvelle conversation"""
    game_id: UUID
    title: str = Field(..., min_length=1, max_length=200, description="Titre de la conversation")


class SendMessageRequest(BaseModel):
    """Request pour envoyer un message"""
    conversation_id: UUID
    content: str = Field(..., min_length=1, max_length=2000, description="Contenu du message utilisateur")


class AddFeedbackRequest(BaseModel):
    """Request pour ajouter un feedback sur un message"""
    feedback_type: FeedbackType
    comment: Optional[str] = Field(None, max_length=500, description="Commentaire optionnel")

    class Config:
        use_enum_values = True


class GetConversationHistoryRequest(BaseModel):
    """Request pour récupérer l'historique d'une conversation"""
    limit: int = Field(20, ge=1, le=100, description="Nombre de messages à récupérer")
    offset: int = Field(0, ge=0, description="Décalage pour la pagination")


# Response schemas
class CreateConversationResponse(BaseModel):
    """Response de création de conversation"""
    success: bool
    conversation: Optional[ChatConversationSchema] = None
    error_message: Optional[str] = None


class SendMessageResponse(BaseModel):
    """Response d'envoi de message"""
    success: bool
    user_message: Optional[ChatMessageSchema] = None
    assistant_message: Optional[ChatMessageSchema] = None
    error_message: Optional[str] = None


class GetConversationHistoryResponse(BaseModel):
    """Response de récupération d'historique"""
    success: bool
    messages: List[ChatMessageSchema] = []
    total_messages: int = 0
    has_more: bool = False
    error_message: Optional[str] = None


class AddFeedbackResponse(BaseModel):
    """Response d'ajout de feedback"""
    success: bool
    feedback: Optional[ChatFeedbackSchema] = None
    error_message: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response pour la liste des conversations d'un utilisateur"""
    success: bool
    conversations: List[ChatConversationSchema] = []
    total_conversations: int = 0
    has_more: bool = False
    error_message: Optional[str] = None


# Status schemas
class ConversationStatsSchema(BaseModel):
    """Schema pour les statistiques d'une conversation"""
    conversation_id: UUID
    total_messages: int
    positive_feedback_count: int
    negative_feedback_count: int
    last_message_at: Optional[datetime] = None