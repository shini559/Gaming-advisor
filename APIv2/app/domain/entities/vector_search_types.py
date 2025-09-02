from enum import Enum


class VectorSearchMethod(Enum):
    """Available search methods"""

    OCR = "ocr"
    DESCRIPTION = "description"
    LABELS = "labels"
    HYBRID = "hybrid"  # COmbines multiple types, not implemented yet
    
    def get_search_method_column(self) -> tuple[str, str]:
        """Returns the corresponding embedding and content column names"""

        if self == VectorSearchMethod.OCR:
            return "ocr_embedding", "ocr_content"
        elif self == VectorSearchMethod.DESCRIPTION:
            return "description_embedding", "description_content"
        elif self == VectorSearchMethod.LABELS:
            return "labels_embedding", "labels_content"
        else:
            raise ValueError(f"Search method unsupported: {self}")
    
    def get_not_null_condition(self) -> str:
        """Returns SQL condition to check if data exists"""

        if self == VectorSearchMethod.OCR:
            return "AND ocr_content IS NOT NULL AND ocr_embedding IS NOT NULL"
        elif self == VectorSearchMethod.DESCRIPTION:
            return "AND description_content IS NOT NULL AND description_embedding IS NOT NULL"
        elif self == VectorSearchMethod.LABELS:
            return "AND labels_content IS NOT NULL AND labels_embedding IS NOT NULL"
        else:
            return ""


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