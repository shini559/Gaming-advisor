from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat_message import MessageSource


@dataclass
class AgentContext:
    """Contexte fourni à l'agent IA"""
    
    game_id: UUID
    conversation_history: List[str]  # Historique formaté pour l'IA
    search_results: List[dict]  # Résultats de recherche vectorielle formatés
    user_question: str
    
    # has_relevant_context() supprimée - l'agent décide directement
    
    def get_context_summary(self) -> str:
        """Retourne un résumé du contexte disponible"""
        if len(self.search_results) == 0:
            return "Aucun contexte trouvé"
        
        return f"{len(self.search_results)} source(s) trouvée(s) dans les règles"


@dataclass
class AgentResponse:
    """Réponse de l'agent IA"""
    
    content: str
    sources: List[MessageSource]
    confidence: float  # Score de confiance entre 0 et 1
    search_method: Optional[str] = None  # Méthode de recherche utilisée
    reasoning: Optional[str] = None  # Explication du raisonnement (pour debug)
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Vérifie si l'agent est confiant dans sa réponse"""
        return self.confidence >= threshold
    
    def has_sources(self) -> bool:
        """Vérifie si la réponse a des sources"""
        return len(self.sources) > 0
    
    def get_sources_summary(self) -> str:
        """Retourne un résumé des sources utilisées"""
        if not self.has_sources():
            return ""
        
        if len(self.sources) == 1:
            return "Source utilisée: règles du jeu"
        
        return f"{len(self.sources)} sources utilisées: règles du jeu"


@dataclass
class AgentRequest:
    """Requête pour l'agent IA"""
    
    conversation_id: UUID
    game_id: UUID
    user_message: str
    include_conversation_history: bool = True
    max_context_length: int = 8000
    
    def validate(self) -> None:
        """Valide la requête"""
        if not self.user_message.strip():
            raise ValueError("Le message utilisateur ne peut pas être vide")
        if self.max_context_length <= 0:
            raise ValueError("La longueur de contexte doit être positive")


class IGameRulesAgent(ABC):
    """Interface pour l'agent IA spécialisé dans les règles de jeux de société"""
    
    @abstractmethod
    async def generate_response(self, request: AgentRequest) -> AgentResponse:
        """
        Génère une réponse à partir d'une question utilisateur
        
        Args:
            request: Requête contenant la question et le contexte
            
        Returns:
            Réponse de l'agent avec sources
        """
        pass
    
    # Méthode supprimée: is_game_rules_question() 
    # L'agent gère naturellement le scope via son prompt système
    
    @abstractmethod
    async def build_context(self, request: AgentRequest) -> AgentContext:
        """
        Construit le contexte pour l'agent IA
        
        Args:
            request: Requête de l'utilisateur
            
        Returns:
            Contexte enrichi avec historique et recherche vectorielle
        """
        pass