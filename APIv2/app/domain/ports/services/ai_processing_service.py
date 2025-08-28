from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Optional
from uuid import UUID

@dataclass
class AIProcessingResult:
  """Résultat du traitement IA d'une image"""
  extracted_text: str                    # OCR
  visual_description: str                # Description des éléments visuels
  labels: list[str]                      # Tags/labels identifiés
  text_embedding: list[float]            # Vecteur du texte extrait
  description_embedding: list[float]     # Vecteur de la description
  success: bool
  error_message: Optional[str] = None

class IAIProcessingService(ABC):
  """Interface pour le service de traitement IA"""

  @abstractmethod
  async def process_image(
      self,
      image_content: BinaryIO,
      filename: str
  ) -> AIProcessingResult:
      """
      Traite une image avec IA : OCR + description + vectorisation

      Args:
          image_content: Contenu binaire de l'image
          filename: Nom du fichier pour context

      Returns:
          AIProcessingResult avec tous les éléments extraits
      """
      pass

  @abstractmethod
  async def test_connection(self) -> tuple[bool, str]:
    """Teste la connexion au service IA
    Returns: (success: bool, message: str)
    """
    pass