from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from app.domain.entities.chat_conversation import ChatConversation
from app.domain.entities.chat_message import ChatMessage
from app.domain.ports.repositories.chat_conversation_repository import IChatConversationRepository
from app.domain.ports.repositories.chat_message_repository import IChatMessageRepository
from app.domain.ports.services.game_rules_agent import IGameRulesAgent, AgentRequest


@dataclass
class SendMessageRequest:
    """Request pour envoyer un message à l'agent IA"""
    
    conversation_id: UUID
    user_id: UUID
    message_content: str
    
    def validate(self) -> None:
        """Valide la requête"""
        if not self.message_content.strip():
            raise ValueError("Le message ne peut pas être vide")
        if len(self.message_content) > 2000:
            raise ValueError("Le message ne peut pas dépasser 2000 caractères")


@dataclass
class SendMessageResponse:
    """Response d'envoi de message"""
    
    success: bool
    user_message: Optional[ChatMessage] = None
    agent_message: Optional[ChatMessage] = None
    error_message: Optional[str] = None
    
    @classmethod
    def success_response(
        cls, 
        user_message: ChatMessage, 
        agent_message: ChatMessage
    ) -> 'SendMessageResponse':
        return cls(
            success=True,
            user_message=user_message,
            agent_message=agent_message
        )
    
    @classmethod
    def error_response(cls, error_message: str) -> 'SendMessageResponse':
        return cls(success=False, error_message=error_message)


class SendMessageUseCase:
    """
    Use case principal pour l'envoi de messages à l'agent IA
    
    Ce use case orchestre tout le flux :
    1. Validation des permissions
    2. Sauvegarde du message utilisateur
    3. Génération de la réponse IA via RAG
    4. Sauvegarde de la réponse IA
    5. Mise à jour de la conversation
    """
    
    def __init__(
        self,
        conversation_repository: IChatConversationRepository,
        message_repository: IChatMessageRepository,
        game_rules_agent: IGameRulesAgent
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.game_rules_agent = game_rules_agent
    
    async def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        """Exécute l'envoi d'un message et génère la réponse de l'agent"""
        try:
            request.validate()
            
            # 1. Vérifier que la conversation existe et appartient à l'utilisateur
            conversation = await self._validate_conversation_access(
                request.conversation_id, 
                request.user_id
            )
            if not conversation:
                return SendMessageResponse.error_response("Conversation non trouvée ou accès refusé")
            
            # 2. Créer et sauvegarder le message utilisateur
            user_message = await self._save_user_message(
                request.conversation_id, 
                request.message_content
            )
            
            # 3. Générer la réponse de l'agent IA
            agent_message = await self._generate_agent_response(
                conversation, 
                request.message_content
            )
            
            # 4. Mettre à jour le timestamp de la conversation
            conversation.touch()
            await self.conversation_repository.update(conversation)
            
            return SendMessageResponse.success_response(user_message, agent_message)
            
        except ValueError as e:
            return SendMessageResponse.error_response(str(e))
        except Exception as e:
            return SendMessageResponse.error_response(f"Erreur lors de l'envoi: {str(e)}")
    
    async def _validate_conversation_access(
        self, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> Optional[ChatConversation]:
        """Valide l'accès à la conversation"""
        if not await self.conversation_repository.exists_for_user(conversation_id, user_id):
            return None
        
        return await self.conversation_repository.get_by_id(conversation_id)
    
    async def _save_user_message(
        self, 
        conversation_id: UUID, 
        content: str
    ) -> ChatMessage:
        """Sauvegarde le message utilisateur"""
        user_message = ChatMessage.create_user_message(
            conversation_id=conversation_id,
            content=content
        )
        
        return await self.message_repository.create(user_message)
    
    async def _generate_agent_response(
        self, 
        conversation: ChatConversation, 
        user_message_content: str
    ) -> ChatMessage:
        """Génère et sauvegarde la réponse de l'agent IA"""
        
        # 1. Préparer la requête pour l'agent
        agent_request = AgentRequest(
            conversation_id=conversation.id,
            game_id=conversation.game_id,
            user_message=user_message_content,
            include_conversation_history=True
        )
        
        # 2. Générer la réponse avec l'agent IA
        agent_response = await self.game_rules_agent.generate_response(agent_request)
        
        # 3. Créer le message assistant avec les sources
        agent_message = ChatMessage.create_assistant_message(
            conversation_id=conversation.id,
            content=agent_response.content,
            sources=agent_response.sources
        )
        
        # 4. Sauvegarder le message assistant
        return await self.message_repository.create(agent_message)