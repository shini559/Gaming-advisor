from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat_message import ChatMessage
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository


@dataclass
class GetConversationHistoryRequest:
    """Request pour récupérer l'historique d'une conversation"""
    
    conversation_id: UUID
    user_id: UUID
    limit: int = 50
    offset: int = 0
    
    def validate(self) -> None:
        """Valide la requête"""
        if self.limit <= 0 or self.limit > 100:
            raise ValueError("La limite doit être entre 1 et 100")
        if self.offset < 0:
            raise ValueError("L'offset ne peut pas être négatif")


@dataclass
class GetConversationHistoryResponse:
    """Response de récupération d'historique"""
    
    success: bool
    messages: Optional[List[ChatMessage]] = None
    total_messages: int = 0
    has_more: bool = False
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(
        cls, 
        messages: List[ChatMessage], 
        total_messages: int,
        has_more: bool
    ) -> 'GetConversationHistoryResponse':
        return cls(
            success=True,
            messages=messages,
            total_messages=total_messages,
            has_more=has_more
        )
    
    @classmethod
    def error_response(cls, error_message: str) -> 'GetConversationHistoryResponse':
        return cls(success=False, error_message=error_message)


class GetConversationHistoryUseCase:
    """
    Use case pour récupérer l'historique d'une conversation
    
    Ce use case :
    1. Valide l'accès à la conversation
    2. Récupère les messages avec pagination
    3. Retourne l'historique ordonné chronologiquement
    """
    
    def __init__(
        self,
        conversation_repository: IChatConversationRepository,
        message_repository: IChatMessageRepository
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
    
    async def execute(self, request: GetConversationHistoryRequest) -> GetConversationHistoryResponse:
        """Exécute la récupération d'historique"""
        try:
            request.validate()
            
            # 1. Vérifier que la conversation existe et appartient à l'utilisateur
            if not await self.conversation_repository.exists_for_user(
                request.conversation_id, 
                request.user_id
            ):
                return GetConversationHistoryResponse.error_response(
                    "Conversation non trouvée ou accès refusé"
                )
            
            # 2. Récupérer le nombre total de messages
            total_messages = await self.message_repository.count_by_conversation(
                request.conversation_id
            )
            
            # 3. Récupérer les messages avec pagination
            messages = await self.message_repository.get_conversation_history(
                conversation_id=request.conversation_id,
                limit_messages=request.limit,
                offset=request.offset
            )
            
            # 4. Déterminer s'il y a plus de messages
            has_more = (request.offset + len(messages)) < total_messages
            
            return GetConversationHistoryResponse.success_response(
                messages=messages,
                total_messages=total_messages,
                has_more=has_more
            )
            
        except ValueError as e:
            return GetConversationHistoryResponse.error_response(str(e))
        except Exception as e:
            return GetConversationHistoryResponse.error_response(
                f"Erreur lors de la récupération: {str(e)}"
            )