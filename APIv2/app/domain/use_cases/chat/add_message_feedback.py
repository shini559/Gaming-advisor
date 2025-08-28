from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.entities.chat_feedback import ChatFeedback, FeedbackType
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository
from app.domain.ports.repositories.chat_feedback_repository import IChatFeedbackRepository
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository


@dataclass
class AddMessageFeedbackRequest:
    """Request pour ajouter un feedback sur un message"""
    
    message_id: UUID
    user_id: UUID
    feedback_type: FeedbackType
    comment: Optional[str] = None
    
    def validate(self) -> None:
        """Valide la requête"""
        if self.comment and len(self.comment) > 500:
            raise ValueError("Le commentaire ne peut pas dépasser 500 caractères")


@dataclass
class AddMessageFeedbackResponse:
    """Response d'ajout de feedback"""
    
    success: bool
    feedback: Optional[ChatFeedback] = None
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(cls, feedback: ChatFeedback) -> 'AddMessageFeedbackResponse':
        return cls(success=True, feedback=feedback)
    
    @classmethod
    def error_response(cls, error_message: str) -> 'AddMessageFeedbackResponse':
        return cls(success=False, error_message=error_message)


class AddMessageFeedbackUseCase:
    """
    Use case pour ajouter un feedback utilisateur sur un message de l'agent
    
    Ce use case :
    1. Valide que le message existe et appartient à l'utilisateur
    2. Vérifie que le message est un message assistant
    3. Crée ou met à jour le feedback
    4. Retourne le feedback créé/mis à jour
    """
    
    def __init__(
        self,
        message_repository: IChatMessageRepository,
        conversation_repository: IChatConversationRepository,
        feedback_repository: IChatFeedbackRepository
    ):
        self.message_repository = message_repository
        self.conversation_repository = conversation_repository
        self.feedback_repository = feedback_repository
    
    async def execute(self, request: AddMessageFeedbackRequest) -> AddMessageFeedbackResponse:
        """Exécute l'ajout/mise à jour de feedback"""
        try:
            request.validate()
            
            # 1. Récupérer le message
            message = await self.message_repository.get_by_id(request.message_id)
            if not message:
                return AddMessageFeedbackResponse.error_response("Message non trouvé")
            
            # 2. Vérifier que le message est un message assistant
            if not message.is_from_assistant():
                return AddMessageFeedbackResponse.error_response(
                    "Le feedback ne peut être donné que sur les messages de l'assistant"
                )
            
            # 3. Vérifier l'accès à la conversation
            if not await self.conversation_repository.exists_for_user(
                message.conversation_id, 
                request.user_id
            ):
                return AddMessageFeedbackResponse.error_response(
                    "Accès à la conversation refusé"
                )
            
            # 4. Vérifier si un feedback existe déjà
            existing_feedback = await self.feedback_repository.get_by_message_and_user(
                request.message_id,
                request.user_id
            )
            
            if existing_feedback:
                # Mise à jour du feedback existant
                existing_feedback.update_feedback(
                    feedback_type=request.feedback_type,
                    comment=request.comment
                )
                updated_feedback = await self.feedback_repository.update(existing_feedback)
                return AddMessageFeedbackResponse.success_response(updated_feedback)
            else:
                # Création d'un nouveau feedback
                feedback = ChatFeedback.create(
                    message_id=request.message_id,
                    user_id=request.user_id,
                    feedback_type=request.feedback_type,
                    comment=request.comment
                )
                
                created_feedback = await self.feedback_repository.create(feedback)
                return AddMessageFeedbackResponse.success_response(created_feedback)
            
        except ValueError as e:
            return AddMessageFeedbackResponse.error_response(str(e))
        except Exception as e:
            return AddMessageFeedbackResponse.error_response(
                f"Erreur lors de l'ajout du feedback: {str(e)}"
            )