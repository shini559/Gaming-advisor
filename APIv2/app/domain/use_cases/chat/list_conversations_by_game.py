from dataclasses import dataclass
from typing import List
from uuid import UUID

from app.domain.entities.chat_conversation import ChatConversation
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository


@dataclass
class ListConversationsByGameRequest:
    """Requête pour lister les conversations d'un utilisateur pour un jeu"""
    user_id: UUID
    game_id: UUID
    limit: int = 20
    offset: int = 0


@dataclass
class ListConversationsByGameResponse:
    """Réponse avec la liste des conversations"""
    success: bool
    conversations: List[ChatConversation] = None
    total_conversations: int = 0
    has_more: bool = False
    error_message: str = None


class ListConversationsByGameUseCase:
    """Use case pour lister les conversations d'un utilisateur pour un jeu donné"""

    def __init__(self, conversation_repository: IChatConversationRepository):
        self.conversation_repository = conversation_repository

    async def execute(self, request: ListConversationsByGameRequest) -> ListConversationsByGameResponse:
        """Exécute la récupération des conversations"""
        try:
            # Valider la requête
            if not request.user_id:
                return ListConversationsByGameResponse(
                    success=False,
                    error_message="ID utilisateur requis"
                )

            if not request.game_id:
                return ListConversationsByGameResponse(
                    success=False,
                    error_message="ID jeu requis"
                )

            if request.limit <= 0 or request.limit > 100:
                return ListConversationsByGameResponse(
                    success=False,
                    error_message="Limit doit être entre 1 et 100"
                )

            # Récupérer les conversations
            conversations = await self.conversation_repository.get_by_game_and_user(
                game_id=request.game_id,
                user_id=request.user_id,
                limit=request.limit,
                offset=request.offset
            )

            # Compter le total pour la pagination
            total_count = await self.conversation_repository.count_by_game_and_user(
                game_id=request.game_id,
                user_id=request.user_id
            )

            has_more = (request.offset + len(conversations)) < total_count

            return ListConversationsByGameResponse(
                success=True,
                conversations=conversations,
                total_conversations=total_count,
                has_more=has_more
            )

        except Exception as e:
            return ListConversationsByGameResponse(
                success=False,
                error_message=f"Erreur lors de la récupération des conversations: {str(e)}"
            )