from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.dependencies.auth import get_current_user
from app.dependencies.use_cases import (
    get_create_conversation_use_case,
    get_send_message_use_case,
    get_conversation_history_use_case,
    get_add_message_feedback_use_case,
    get_list_conversations_by_game_use_case
)
from app.domain.entities.user import User
from app.domain.use_cases.chat.create_conversation import CreateConversationUseCase, CreateConversationRequest as UseCaseCreateRequest
from app.domain.use_cases.chat.send_message import SendMessageUseCase, SendMessageRequest as UseCaseSendRequest
from app.domain.use_cases.chat.get_conversation_history import GetConversationHistoryUseCase, GetConversationHistoryRequest as UseCaseHistoryRequest
from app.domain.use_cases.chat.add_message_feedback import AddMessageFeedbackUseCase, AddMessageFeedbackRequest as UseCaseFeedbackRequest
from app.domain.use_cases.chat.list_conversations_by_game import ListConversationsByGameUseCase, ListConversationsByGameRequest as UseCaseListRequest
from app.presentation.schemas.chat import (
    CreateConversationRequest,
    CreateConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    GetConversationHistoryRequest,
    GetConversationHistoryResponse,
    AddFeedbackRequest,
    AddFeedbackResponse,
    ChatMessageSchema,
    ChatConversationSchema,
    ChatFeedbackSchema,
    MessageSourceSchema,
    ConversationListResponse
)

router = APIRouter(prefix="/chat", tags=["Chat"])


def _convert_message_to_schema(message) -> ChatMessageSchema:
    """Convertit un message domain en schema"""
    sources = None
    if message.sources:
        sources = [
            MessageSourceSchema(
                vector_id=source.vector_id,
                image_id=source.image_id,
                similarity_score=source.similarity_score,
                content_snippet=source.content_snippet,
                image_url=source.image_url
            )
            for source in message.sources
        ]
    
    return ChatMessageSchema(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        sources=sources,
        search_method=message.search_method,
        is_useful=message.is_useful,
        created_at=message.created_at
    )


def _convert_conversation_to_schema(conversation) -> ChatConversationSchema:
    """Convertit une conversation domain en schema"""
    return ChatConversationSchema(
        id=conversation.id,
        game_id=conversation.game_id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


def _convert_feedback_to_schema(feedback) -> ChatFeedbackSchema:
    """Convertit un feedback domain en schema"""
    return ChatFeedbackSchema(
        id=feedback.id,
        message_id=feedback.message_id,
        feedback_type=feedback.feedback_type,
        comment=feedback.comment,
        created_at=feedback.created_at
    )


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateConversationUseCase = Depends(get_create_conversation_use_case)
) -> CreateConversationResponse:
    """Créer une nouvelle conversation de chat pour un jeu"""
    
    use_case_request = UseCaseCreateRequest(
        game_id=request.game_id,
        user_id=current_user.id,
        title=request.title
    )
    
    result = await use_case.execute(use_case_request)
    
    if result.success:
        conversation_schema = _convert_conversation_to_schema(result.conversation)
        return CreateConversationResponse(
            success=True,
            conversation=conversation_schema
        )
    else:
        return CreateConversationResponse(
            success=False,
            error_message=result.error_message
        )


@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    use_case: SendMessageUseCase = Depends(get_send_message_use_case)
) -> SendMessageResponse:
    """Envoyer un message dans une conversation"""
    
    use_case_request = UseCaseSendRequest(
        conversation_id=request.conversation_id,
        user_id=current_user.id,
        message_content=request.content
    )
    
    result = await use_case.execute(use_case_request)
    
    if result.success:
        user_message_schema = _convert_message_to_schema(result.user_message)
        assistant_message_schema = _convert_message_to_schema(result.agent_message)
        
        return SendMessageResponse(
            success=True,
            user_message=user_message_schema,
            assistant_message=assistant_message_schema
        )
    else:
        return SendMessageResponse(
            success=False,
            error_message=result.error_message
        )


@router.get("/conversations/{conversation_id}/history", response_model=GetConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: UUID,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    use_case: GetConversationHistoryUseCase = Depends(get_conversation_history_use_case)
) -> GetConversationHistoryResponse:
    """Récupérer l'historique des messages d'une conversation"""
    
    use_case_request = UseCaseHistoryRequest(
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    result = await use_case.execute(use_case_request)
    
    if result.success:
        messages_schema = [_convert_message_to_schema(msg) for msg in result.messages]
        
        return GetConversationHistoryResponse(
            success=True,
            messages=messages_schema,
            total_messages=result.total_messages,
            has_more=result.has_more
        )
    else:
        return GetConversationHistoryResponse(
            success=False,
            error_message=result.error_message
        )


@router.post("/messages/{message_id}/feedback", response_model=AddFeedbackResponse)
async def add_message_feedback(
    message_id: UUID,
    request: AddFeedbackRequest,
    current_user: User = Depends(get_current_user),
    use_case: AddMessageFeedbackUseCase = Depends(get_add_message_feedback_use_case)
) -> AddFeedbackResponse:
    """Ajouter un feedback (satisfaction) sur un message de l'assistant"""
    
    use_case_request = UseCaseFeedbackRequest(
        message_id=message_id,
        user_id=current_user.id,
        feedback_type=request.feedback_type,
        comment=request.comment
    )
    
    result = await use_case.execute(use_case_request)
    
    if result.success:
        feedback_schema = _convert_feedback_to_schema(result.feedback)
        return AddFeedbackResponse(
            success=True,
            feedback=feedback_schema
        )
    else:
        return AddFeedbackResponse(
            success=False,
            error_message=result.error_message
        )


@router.get("/games/{game_id}/conversations", response_model=ConversationListResponse)
async def list_conversations_by_game(
    game_id: UUID,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    use_case: ListConversationsByGameUseCase = Depends(get_list_conversations_by_game_use_case)
) -> ConversationListResponse:
    """Récupérer les conversations de l'utilisateur actuel pour un jeu spécifique"""
    
    use_case_request = UseCaseListRequest(
        user_id=current_user.id,
        game_id=game_id,
        limit=limit,
        offset=offset
    )
    
    result = await use_case.execute(use_case_request)
    
    if result.success:
        conversations_schema = [_convert_conversation_to_schema(conv) for conv in result.conversations]
        
        return ConversationListResponse(
            success=True,
            conversations=conversations_schema,
            total_conversations=result.total_conversations,
            has_more=result.has_more
        )
    else:
        return ConversationListResponse(
            success=False,
            error_message=result.error_message
        )