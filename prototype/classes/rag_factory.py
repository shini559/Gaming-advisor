from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional

from classes.rag_manager import RAGManager
from classes.hybrid_rag_manager import HybridRAGManager


class RAGType(Enum):
    """Types de RAG disponibles"""
    CLASSIC = "classic"
    HYBRID = "hybrid"
    DIRECT = "direct"


class BaseRAGInterface(ABC):
    """Interface commune pour tous les types de RAG"""
    
    @abstractmethod
    def process_game_document(self, images_data):
        """Traite et stocke un document de jeu"""
        pass
    
    @abstractmethod
    def retrieve_relevant_rules(self, user_query, game_context=None):
        """Recherche du contexte pertinent pour une question"""
        pass
    
    @abstractmethod
    def clear_vector_store(self):
        """Vide le store vectoriel"""
        pass
    
    @abstractmethod
    def get_vector_store_info(self):
        """Retourne des infos sur le store"""
        pass


class ClassicRAGAdapter(BaseRAGInterface):
    """Adaptateur pour le RAG classique"""
    
    def __init__(self, settings, game_name=None):
        # Créer un settings adapté avec les modèles RAG classique
        rag_settings = self._create_rag_settings(settings, game_name)
        self.rag_manager = RAGManager(rag_settings)
        self.rag_type = RAGType.CLASSIC
    
    def _create_rag_settings(self, settings, game_name=None):
        """Crée un objet settings avec les modèles RAG classique"""
        class RAGSettings:
            def __init__(self, base_settings):
                # Copier les paramètres de base
                self.params = base_settings.params.copy()
                # Utiliser les modèles RAG classique
                self.rag_vision_model = base_settings.rag_vision_model
                # Pour les embeddings, on doit configurer directement l'objet
                self.rag_embedding_model = base_settings.rag_embedding_model
                # Copier les prompts depuis les settings
                self.rag_vision_prompt = base_settings.rag_vision_prompt
                
        return RAGSettings(settings)
    
    def process_game_document(self, images_data):
        return self.rag_manager.process_game_document(images_data)
    
    def retrieve_relevant_rules(self, user_query, game_context=None):
        context = self.rag_manager.retrieve_relevant_rules(user_query, game_context)
        # Format unifié : toujours retourner un dict
        if context:
            return {
                "type": "text",
                "context": context,
                "images": None,
                "image_count": 0
            }
        return None
    
    def clear_vector_store(self):
        self.rag_manager.clear_vector_store()
    
    def get_vector_store_info(self):
        info = self.rag_manager.get_vector_store_info()
        info["rag_type"] = "Classique (Texte)"
        return info
    
    @property
    def embeddings(self):
        """Pour compatibilité avec le code existant"""
        return self.rag_manager.embeddings
    
    @property
    def vector_store(self):
        """Pour compatibilité avec le code existant"""
        return self.rag_manager.vector_store


class HybridRAGAdapter(BaseRAGInterface):
    """Adaptateur pour le RAG hybride"""
    
    def __init__(self, settings, game_name=None):
        # Créer un settings adapté avec les modèles RAG hybride
        hybrid_settings = self._create_hybrid_settings(settings, game_name)
        self.rag_manager = HybridRAGManager(hybrid_settings, game_name)
        self.rag_type = RAGType.HYBRID
    
    def _create_hybrid_settings(self, settings, game_name=None):
        """Crée un objet settings avec les modèles RAG hybride"""
        class HybridSettings:
            def __init__(self, base_settings):
                # Copier les paramètres de base
                self.params = base_settings.params.copy()
                # Utiliser les modèles RAG hybride
                self.hybrid_vision_model = base_settings.hybrid_vision_model
                # Pour les embeddings hybride
                self.hybrid_embedding_model = base_settings.hybrid_embedding_model
                # Utiliser l'agent principal pour toutes les méthodes
                self.agent_model = base_settings.agent_model
                # Copier le prompt vision hybride
                self.hybrid_vision_prompt = base_settings.hybrid_vision_prompt
                
        return HybridSettings(settings)
    
    def process_game_document(self, images_data):
        return self.rag_manager.process_game_document(images_data)
    
    def retrieve_relevant_rules(self, user_query, game_context=None):
        result = self.rag_manager.retrieve_relevant_images(user_query)
        # Format unifié : toujours retourner un dict
        if result:
            return {
                "type": "hybrid",
                "context": result.get("context"),
                "images": result.get("images", []),
                "image_count": result.get("image_count", 0)
            }
        return None
    
    def clear_vector_store(self):
        self.rag_manager.clear_vector_store()
    
    def get_vector_store_info(self):
        info = self.rag_manager.get_vector_store_info()
        info["rag_type"] = "Hybride (Métadonnées + Images)"
        return info
    
    @property
    def embeddings(self):
        """Pour compatibilité avec le code existant"""
        return self.rag_manager.embeddings
    
    @property
    def vector_store(self):
        """Pour compatibilité avec le code existant"""
        return self.rag_manager.vector_store


class DirectRAGAdapter(BaseRAGInterface):
    """Adaptateur pour le mode direct (pas de RAG, envoi direct des images)"""
    
    def __init__(self, settings, game_name=None):
        self.settings = settings
        self.game_name = game_name
        self.rag_type = RAGType.DIRECT
        self.stored_images = []  # Stockage temporaire des images
    
    def process_game_document(self, images_data):
        """Stocke les images pour envoi direct (pas de vectorisation)"""
        if images_data:
            self.stored_images.extend(images_data)
            return {"success": True, "message": f"{len(images_data)} image(s) prête(s) pour envoi direct"}
        return {"success": False, "message": "Aucune image fournie"}
    
    def retrieve_relevant_rules(self, user_query, game_context=None):
        """Retourne toutes les images stockées pour envoi direct"""
        if self.stored_images:
            return {
                "type": "direct",
                "context": "Mode direct: toutes les images seront envoyées au modèle",
                "images": self.stored_images,
                "image_count": len(self.stored_images)
            }
        return None
    
    def clear_vector_store(self):
        """Vide le stockage des images"""
        self.stored_images = []
    
    def get_vector_store_info(self):
        """Retourne les infos sur les images stockées"""
        return {
            "rag_type": "Direct (Pas de RAG)",
            "document_count": 0,
            "image_count": len(self.stored_images)
        }
    
    @property
    def embeddings(self):
        """Mode direct : pas d'embeddings"""
        return None
    
    @property
    def vector_store(self):
        """Mode direct : pas de vector store"""
        return None


class RAGFactory:
    """Factory pour créer et gérer les différents types de RAG"""
    
    _instances = {}
    _current_rag = None
    _current_type = None
    
    @classmethod
    def create_rag(cls, rag_type: RAGType, settings, force_recreate=False, game_name: str = None) -> BaseRAGInterface:
        """
        Crée ou récupère une instance RAG du type spécifié
        
        Args:
            rag_type: Type de RAG à créer
            settings: Configuration
            force_recreate: Force la recréation même si existe
            
        Returns:
            Instance RAG du type demandé
        """
        type_key = rag_type.value
        
        # Si on force la recréation ou si l'instance n'existe pas
        if force_recreate or type_key not in cls._instances:
            print(f"🏭 RAGFactory: {'Recréation' if force_recreate else 'Création'} {rag_type.value}")
            
            # Nettoyer l'ancienne instance si elle existe (important pour éviter les fuites mémoire)
            if force_recreate and type_key in cls._instances:
                old_instance = cls._instances[type_key]
                print(f"🧹 RAGFactory: Nettoyage ancienne instance {rag_type.value}")
                # Permettre au garbage collector de nettoyer
                del old_instance
            
            if rag_type == RAGType.CLASSIC:
                cls._instances[type_key] = ClassicRAGAdapter(settings, game_name)
            elif rag_type == RAGType.HYBRID:
                cls._instances[type_key] = HybridRAGAdapter(settings, game_name)
            elif rag_type == RAGType.DIRECT:
                cls._instances[type_key] = DirectRAGAdapter(settings, game_name)
            else:
                raise ValueError(f"Type RAG non supporté: {rag_type}")
        
        cls._current_rag = cls._instances[type_key]
        cls._current_type = rag_type
        print(f"✅ RAGFactory: RAG actuel = {rag_type.value}")
        
        return cls._current_rag
    
    @classmethod
    def get_current_rag(cls) -> Optional[BaseRAGInterface]:
        """Retourne le RAG actuellement actif"""
        return cls._current_rag
    
    @classmethod
    def get_current_type(cls) -> Optional[RAGType]:
        """Retourne le type de RAG actuellement actif"""
        return cls._current_type
    
    @classmethod
    def switch_rag_type(cls, new_type: RAGType, settings) -> BaseRAGInterface:
        """Change de type de RAG"""
        if cls._current_type == new_type and cls._current_rag:
            print(f"ℹ️ RAGFactory: Déjà en mode {new_type.value}")
            return cls._current_rag
        
        print(f"🔄 RAGFactory: Changement {cls._current_type.value if cls._current_type else 'None'} → {new_type.value}")
        return cls.create_rag(new_type, settings)
    
    @classmethod
    def get_available_types(cls) -> Dict[str, str]:
        """Retourne les types RAG disponibles avec leurs descriptions"""
        return {
            RAGType.CLASSIC.value: "RAG Classique - Texte vectorisé",
            RAGType.HYBRID.value: "RAG Hybride - Métadonnées + Images directes",
            RAGType.DIRECT.value: "Mode Direct - Images envoyées directement sans RAG"
        }
    
    @classmethod
    def clear_all_stores(cls):
        """Vide tous les stores RAG existants"""
        cleared = []
        for rag_type, rag_instance in cls._instances.items():
            try:
                rag_instance.clear_vector_store()
                cleared.append(rag_type)
            except Exception as e:
                print(f"❌ RAGFactory: Erreur vidage {rag_type}: {e}")
        
        if cleared:
            print(f"🗑️ RAGFactory: Stores vidés: {', '.join(cleared)}")
        else:
            print("⚠️ RAGFactory: Aucun store à vider")
    
    @classmethod
    def get_all_store_info(cls) -> Dict[str, Any]:
        """Retourne les infos de tous les stores RAG"""
        info = {}
        for rag_type, rag_instance in cls._instances.items():
            try:
                info[rag_type] = rag_instance.get_vector_store_info()
            except Exception as e:
                info[rag_type] = {"error": str(e)}
        
        return info
    
    @classmethod
    def reset_factory(cls):
        """Remet à zéro la factory (pour tests)"""
        cls._instances = {}
        cls._current_rag = None
        cls._current_type = None
        print("🔄 RAGFactory: Factory réinitialisée")


# Fonctions utilitaires pour faciliter l'usage

def create_classic_rag(settings):
    """Raccourci pour créer un RAG classique"""
    return RAGFactory.create_rag(RAGType.CLASSIC, settings)

def create_hybrid_rag(settings):
    """Raccourci pour créer un RAG hybride"""
    return RAGFactory.create_rag(RAGType.HYBRID, settings)

def get_rag_type_from_string(type_str: str) -> RAGType:
    """Convertit une string en RAGType"""
    type_mapping = {
        "classic": RAGType.CLASSIC,
        "classique": RAGType.CLASSIC,
        "hybrid": RAGType.HYBRID,
        "hybride": RAGType.HYBRID,
        "direct": RAGType.DIRECT,
        "directe": RAGType.DIRECT
    }
    
    return type_mapping.get(type_str.lower(), RAGType.CLASSIC)