from enum import Enum


class VectorSearchType(Enum):
    """Types de recherche vectorielle disponibles"""
    OCR = "ocr"
    DESCRIPTION = "description"
    LABELS = "labels"
    HYBRID = "hybrid"  # Combine plusieurs types selon un algorithme
    
    def get_embedding_column(self) -> str:
        """Retourne le nom de la colonne d'embedding correspondante"""
        if self == VectorSearchType.OCR:
            return "ocr_embedding"
        elif self == VectorSearchType.DESCRIPTION:
            return "description_embedding"
        elif self == VectorSearchType.LABELS:
            return "labels_embedding"
        else:
            raise ValueError(f"Type de recherche non supporté pour colonne unique: {self}")
    
    def get_content_column(self) -> str:
        """Retourne le nom de la colonne de contenu correspondante"""
        if self == VectorSearchType.OCR:
            return "ocr_content"
        elif self == VectorSearchType.DESCRIPTION:
            return "description_content"
        elif self == VectorSearchType.LABELS:
            return "labels_content"
        else:
            raise ValueError(f"Type de recherche non supporté pour colonne unique: {self}")
    
    def get_not_null_condition(self) -> str:
        """Retourne la condition SQL pour vérifier que les données existent"""
        if self == VectorSearchType.OCR:
            return "AND ocr_content IS NOT NULL AND ocr_embedding IS NOT NULL"
        elif self == VectorSearchType.DESCRIPTION:
            return "AND description_content IS NOT NULL AND description_embedding IS NOT NULL"
        elif self == VectorSearchType.LABELS:
            return "AND labels_content IS NOT NULL AND labels_embedding IS NOT NULL"
        else:
            return ""


class ProcessingType(Enum):
    """Types de traitement IA disponibles"""
    OCR = "ocr"
    VISUAL_DESCRIPTION = "description"
    METADATA_LABELS = "labels"
    
    def get_config_flag(self) -> str:
        """Retourne le nom du flag de configuration correspondant"""
        if self == ProcessingType.OCR:
            return "enable_ocr"
        elif self == ProcessingType.VISUAL_DESCRIPTION:
            return "enable_visual_description"
        elif self == ProcessingType.METADATA_LABELS:
            return "enable_labeling"
        else:
            raise ValueError(f"Type de processing non reconnu: {self}")