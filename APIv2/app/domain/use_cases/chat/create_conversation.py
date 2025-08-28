from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.config import settings
from app.domain.entities.chat_conversation import ChatConversation
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository
from app.domain.ports.repositories.game_repository import IGameRepository


@dataclass
class CreateConversationRequest:
    """Request pour créer une nouvelle conversation"""
    
    game_id: UUID
    user_id: UUID
    title: Optional[str] = None
    
    def validate(self) -> None:
        """Valide la requête"""
        if self.title and len(self.title) > settings.chat_max_title_length:
            raise ValueError(f"Le titre ne peut pas dépasser {settings.chat_max_title_length} caractères")


@dataclass
class CreateConversationResponse:
    """Response de création de conversation"""
    
    success: bool
    conversation: Optional[ChatConversation] = None
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, conversation: ChatConversation) -> 'CreateConversationResponse':
        return cls(success=True, conversation=conversation)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'CreateConversationResponse':
        return cls(success=False, error_message=error_message)


class CreateConversationUseCase:
    """Use case pour créer une nouvelle conversation de chat avec l'agent IA"""
    
    def __init__(
        self,
        conversation_repository: IChatConversationRepository,
        game_repository: IGameRepository
    ):
        self.conversation_repository = conversation_repository
        self.game_repository = game_repository
    
    async def execute(self, request: CreateConversationRequest) -> CreateConversationResponse:
        """Exécute la création d'une nouvelle conversation"""
        try:
            request.validate()
            
            # 1. Vérifier que le jeu existe et est accessible à l'utilisateur
            game = await self.game_repository.get_by_id(request.game_id)
            if not game:
                return CreateConversationResponse.error_response("Jeu non trouvé")
            
            # Vérifier l'accès au jeu (public ou propriétaire)
            if not game.is_public and game.created_by != request.user_id:
                return CreateConversationResponse.error_response("Accès au jeu non autorisé")
            
            # 2. Générer un titre par défaut si non fourni
            title = request.title or self._generate_default_title(game.title)
            
            # 3. Créer l'entité conversation
            conversation = ChatConversation.create(
                game_id=request.game_id,
                user_id=request.user_id,
                title=title
            )
            
            # 4. Sauvegarder en base
            saved_conversation = await self.conversation_repository.create(conversation)
            
            return CreateConversationResponse.success_response(saved_conversation)
            
        except ValueError as e:
            return CreateConversationResponse.error_response(str(e))
        except Exception as e:
            return CreateConversationResponse.error_response(f"Erreur lors de la création: {str(e)}")
    
    def _generate_default_title(self, game_title: str) -> str:
        """Génère un titre par défaut pour la conversation"""
        if game_title:
            return f"Questions sur {game_title}"
        return settings.chat_default_title