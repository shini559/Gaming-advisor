from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Optional
from uuid import UUID

@dataclass
class AIProcessingResult:
  """
  Résultat du traitement IA d'une image - Architecture 3-paires
  Chaque type de contenu a ses données + embedding dédiés
  """
  # === OCR (Optical Character Recognition) ===
  ocr_content: Optional[str] = None
  ocr_embedding: Optional[list[float]] = None
  
  # === Description visuelle ===
  description_content: Optional[str] = None
  description_embedding: Optional[list[float]] = None
  
  # === Métadonnées/Labels ===
  labels_content: Optional[str] = None  # JSON string des métadonnées
  labels_embedding: Optional[list[float]] = None
  
  # === Métadonnées globales ===
  success: bool = True
  error_message: Optional[str] = None
  
  def has_any_data(self) -> bool:
      """Vérifie si au moins un type de données a été extrait"""
      return bool(
          self.ocr_content or 
          self.description_content or 
          self.labels_content
      )
  
  def get_extracted_types(self) -> list[str]:
      """Retourne la liste des types de données extraites avec succès"""
      types = []
      if self.ocr_content and self.ocr_embedding:
          types.append("ocr")
      if self.description_content and self.description_embedding:
          types.append("description")
      if self.labels_content and self.labels_embedding:
          types.append("labels")
      return types

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