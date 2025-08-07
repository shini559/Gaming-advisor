import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings


@dataclass
class Settings:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __post_init__(self):
        if self._initialized:
            return
        load_dotenv(override=True)
        self._initialized = True
    
    @classmethod
    def get_instance(cls):
        """Récupère l'instance globale des settings"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # General parameters
    params = {
        'debug': False,
        'image_max_size': 1024,
        'dpi': 100,
        'chroma_persist_directory': './chroma_db'
    }

    load_dotenv()

    # Modèle principal de l'agent (utilisé pour les réponses finales)
    agent_model = AzureChatOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint="https://gameadvisorai.openai.azure.com/",
        api_key=os.getenv("SUBSCRIPTION_KEY"),
        deployment_name="agent-gpt-4o"
    )

    # === MODÈLES RAG CLASSIQUE ===
    # Modèle pour la vision/analyse des documents (extraction de texte des images)
    rag_vision_model = AzureChatOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint="https://gameadvisorai.openai.azure.com/",
        api_key=os.getenv("SUBSCRIPTION_KEY"),
        deployment_name="rag_vision-gpt-4o"
    )
    
    # Modèle pour les embeddings du RAG classique
    rag_embedding_model = AzureOpenAIEmbeddings(
        api_version="2024-12-01-preview",
        azure_endpoint="https://gameadvisorai.openai.azure.com/",
        api_key=os.getenv("SUBSCRIPTION_KEY"),
        deployment="rag_embedding-text-embedding-3-large"
    )

    # === MODÈLES RAG HYBRIDE ===
    # Modèle pour la vision/analyse des documents hybrides
    hybrid_vision_model = AzureChatOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint="https://gameadvisorai.openai.azure.com/",
        api_key=os.getenv("SUBSCRIPTION_KEY"),
        deployment_name="hybrid_vision-gpt-4o"
    )
    
    # Modèle pour les embeddings du RAG hybride
    hybrid_embedding_model = AzureOpenAIEmbeddings(
        api_version="2024-12-01-preview",
        azure_endpoint="https://gameadvisorai.openai.azure.com/",
        api_key=os.getenv("SUBSCRIPTION_KEY"),
        deployment="hybrid_embedding-text-embedding-3-large"
    )

    # === MODÈLE RAG DIRECT ===
    # En mode direct, on utilise directement l'agent_model principal
    # (pas besoin de modèle séparé car pas de RAG)

    system_prompt: str = '''You are a game master & boardgame assistant. Your role is to assist board gamers in setting up their games, understanding the rules, calculate the score.

The users will send you data. You will analyze this data and use it to answer their questions. ONLY USE THE DATA THEY PROVIDE TO ANSWER THEIR QUESTIONS! YOU MUST NEVER ANSWER A QUESTION ABOUT GAME RULES IF YOU HAVE NOT BEEN PROVIDED DATA BY THE USER!

Answer questions clearly and directly. Use simple French. Ask questions if you need clarification.'''

    @classmethod
    def get_models_info(cls):
        """Retourne un résumé des modèles configurés pour chaque méthode RAG"""
        instance = cls.get_instance()
        
        return {
            "agent_principal": {
                "nom": "Agent principal",
                "model": instance.agent_model.deployment_name,
                "usage": "Réponses finales à l'utilisateur"
            },
            "rag_classique": {
                "vision_model": instance.rag_vision_model.deployment_name,
                "embedding_model": getattr(instance.rag_embedding_model, 'deployment', 'embedding-non-configuré'),
                "usage": "RAG classique - extraction de texte et vectorisation"
            },
            "rag_hybride": {
                "vision_model": instance.hybrid_vision_model.deployment_name,
                "embedding_model": getattr(instance.hybrid_embedding_model, 'deployment', 'embedding-non-configuré'),
                "usage": "RAG hybride - métadonnées + images directes"
            },
            "mode_direct": {
                "model": instance.agent_model.deployment_name,
                "usage": "Mode direct - utilise le modèle agent principal"
            }
        }