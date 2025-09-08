from enum import Enum
from typing import List


class VectorSearchMethod(Enum):
    """Méthodes de recherche vectorielle découplées - SEULEMENT pour la similarité"""

    OCR = "ocr"
    DESCRIPTION = "description"
    LABELS = "labels"
    
    def get_embedding_column(self) -> str:
        """Retourne SEULEMENT la colonne embedding pour la recherche de similarité"""
        mapping = {
            VectorSearchMethod.OCR: "ocr_embedding",
            VectorSearchMethod.DESCRIPTION: "description_embedding", 
            VectorSearchMethod.LABELS: "labels_embedding"
        }
        return mapping[self]
    
    def get_not_null_condition(self) -> str:
        """Condition SQL pour vérifier que l'embedding existe"""
        mapping = {
            VectorSearchMethod.OCR: "AND ocr_embedding IS NOT NULL",
            VectorSearchMethod.DESCRIPTION: "AND description_embedding IS NOT NULL",
            VectorSearchMethod.LABELS: "AND labels_embedding IS NOT NULL"
        }
        return mapping[self]


class AgentContentField(Enum):
    """Champs de contenu disponibles pour l'agent - DÉCOUPLÉS de la recherche"""
    
    OCR = "ocr"
    DESCRIPTION = "description"
    LABELS = "labels"
    
    def get_content_column(self) -> str:
        """Retourne la colonne de contenu correspondante"""
        mapping = {
            AgentContentField.OCR: "ocr_content",
            AgentContentField.DESCRIPTION: "description_content",
            AgentContentField.LABELS: "labels_content"
        }
        return mapping[self]
    
    @classmethod
    def get_content_columns(cls, fields: List[str]) -> List[str]:
        """Retourne les colonnes de contenu pour une liste de champs"""
        columns = []
        for field_str in fields:
            try:
                field = cls(field_str)
                columns.append(field.get_content_column())
            except ValueError:
                continue  # Ignore les champs invalides
        return columns


class ProcessingType(Enum):
    """Available AI treatments"""

    OCR = "ocr"
    VISUAL_DESCRIPTION = "description"
    METADATA_LABELS = "labels"
    
    def get_config_flag(self) -> str:
        """Returns the corresponding config flag (found in config.py). Used to activate/deactivate AI treatments on upload"""
        if self == ProcessingType.OCR:
            return "enable_ocr"
        elif self == ProcessingType.VISUAL_DESCRIPTION:
            return "enable_visual_description"
        elif self == ProcessingType.METADATA_LABELS:
            return "enable_labeling"
        else:
            raise ValueError(f"Type de processing non reconnu: {self}")