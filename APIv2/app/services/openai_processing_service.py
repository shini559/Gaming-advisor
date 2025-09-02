import base64
from io import BytesIO
from typing import BinaryIO, Optional
import asyncio

from openai import AsyncAzureOpenAI
from PIL import Image

from app.config import settings
from app.domain.entities.vector_search_types import ProcessingType
from app.domain.ports.services.ai_processing_service import IAIProcessingService, AIProcessingResult


class OpenAIProcessingService(IAIProcessingService):
  """Service de traitement IA utilisant OpenAI GPT-4 Vision et Embeddings"""

  def __init__(self):
      self._client: Optional[AsyncAzureOpenAI] = None

  @property
  def client(self) -> AsyncAzureOpenAI:
      """Lazy initialization du client Azure OpenAI"""
      if self._client is None:
          if not settings.azure_openai_api_key:
              raise ValueError("Azure OpenAI API key not configured")
          if not settings.azure_openai_endpoint:
              raise ValueError("Azure OpenAI endpoint not configured")
          
          self._client = AsyncAzureOpenAI(
              api_key=settings.azure_openai_api_key,
              azure_endpoint=settings.azure_openai_endpoint,
              api_version=settings.azure_openai_vision_api_version
          )
      return self._client

  async def process_image(
          self,
          image_content: BinaryIO,
          filename: str
  ) -> AIProcessingResult:
      """Traite une image avec OpenAI : OCR + description + vectorisation"""

      try:
          # Préparer l'image pour OpenAI
          image_content.seek(0)
          image_data = image_content.read()

          # Redimensionner si nécessaire (OpenAI a des limites)
          processed_image = await self._prepare_image(image_data)
          image_base64 = base64.b64encode(processed_image).decode('utf-8')

          result = AIProcessingResult()

          # Traitement en parallèle selon configuration
          processing_tasks = []

          processing_config = [
              (ProcessingType.OCR, "ocr", self._extract_text),
              (ProcessingType.VISUAL_DESCRIPTION, "description", self._describe_image),
              (ProcessingType.METADATA_LABELS, "labels", self._label_image)
          ]

          # Activate/deactivate processing methods according to settings
          for processing_type, task_name, method in processing_config:
              config_flag = processing_type.get_config_flag()
              if getattr(settings, config_flag):
                  processing_tasks.append((task_name, method(image_base64)))


          # Phase 1 : Extraction du contenu

          if processing_tasks:
              processing_results = await asyncio.gather(*[task[1] for task in processing_tasks])
              
              for i, (task_type, _) in enumerate(processing_tasks):
                  if task_type == "ocr":
                      result.ocr_content = processing_results[i]
                  elif task_type == "description":
                      result.description_content = processing_results[i]  
                  elif task_type == "labels":
                      # Convertir labels en JSON string si nécessaire
                      labels_data = processing_results[i]
                      if isinstance(labels_data, str):
                          result.labels_content = labels_data
                      else:
                          result.labels_content = str(labels_data)
          
          # Phase 2 : Vectorisation en parallèle
          embedding_tasks = []
          
          if result.ocr_content:
              embedding_tasks.append(("ocr", self._create_embedding(result.ocr_content)))
          if result.description_content:
              embedding_tasks.append(("description", self._create_embedding(result.description_content)))
          if result.labels_content:
              # Convertir JSON en texte searchable pour embedding
              labels_text = self._labels_to_searchable_text(result.labels_content)
              if labels_text:
                  embedding_tasks.append(("labels", self._create_embedding(labels_text)))
          
          # Exécuter la vectorisation
          if embedding_tasks:
              embedding_results = await asyncio.gather(*[task[1] for task in embedding_tasks])
              
              for i, (emb_type, _) in enumerate(embedding_tasks):
                  if emb_type == "ocr":
                      result.ocr_embedding = embedding_results[i]
                  elif emb_type == "description":
                      result.description_embedding = embedding_results[i]
                  elif emb_type == "labels":
                      result.labels_embedding = embedding_results[i]

          return result

      except Exception as e:
          return AIProcessingResult(
              success=False,
              error_message=str(e)
          )

  async def _prepare_image(self, image_data: bytes) -> bytes:
      """Prépare l'image selon les spécifications OpenAI"""
      with Image.open(BytesIO(image_data)) as img:
          # Convertir en RGB si nécessaire
          if img.mode != 'RGB':
              img = img.convert('RGB')

          # Redimensionner selon la config
          target_size = settings.image_processing_resolution
          img.thumbnail(target_size, Image.Resampling.LANCZOS)

          # Sauvegarder en JPEG optimisé
          output = BytesIO()
          img.save(output, format='JPEG', quality=85, optimize=True)
          return output.getvalue()

  async def _extract_text(self, image_base64: str) -> str:
      """Extrait le texte de l'image (OCR)"""
      try:
          response = await self.client.chat.completions.create(
              model=settings.azure_openai_vision_deployment,
              messages=[
                  {
                      "role": "user",
                      "content": [
                          {"type": "text", "text": settings.ocr_prompt},
                          {
                              "type": "image_url",
                              "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                          }
                      ]
                  }
              ],
              max_tokens=1500
          )
          return response.choices[0].message.content or ""
      except Exception as e:
          print(f"OCR Error: {e}")
          return ""

  async def _describe_image(self, image_base64: str) -> str:
      """Décrit les éléments visuels de l'image"""
      try:
          response = await self.client.chat.completions.create(
              model=settings.azure_openai_vision_deployment,
              messages=[
                  {
                      "role": "user",
                      "content": [
                          {"type": "text", "text": settings.vision_description_prompt},
                          {
                              "type": "image_url",
                              "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                          }
                      ]
                  }
              ],
              max_tokens=800
          )
          return response.choices[0].message.content or ""
      except Exception as e:
          print(f"Description Error: {e}")
          return ""

  async def _label_image(self, image_base64: str) -> list[str]:
      """Identifie et labellise les composants de l'image"""
      try:
          response = await self.client.chat.completions.create(
              model=settings.azure_openai_vision_deployment,
              messages=[
                  {
                      "role": "user",
                      "content": [
                          {"type": "text", "text": settings.vision_labeling_prompt},
                          {
                              "type": "image_url",
                              "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                          }
                      ]
                  }
              ],
              max_tokens=300
          )

          labels_text = response.choices[0].message.content or ""
          # Parse les labels séparés par des virgules
          return [label.strip() for label in labels_text.split(',') if label.strip()]
      except Exception as e:
          print(f"Labeling Error: {e}")
          return []

  async def _create_embedding(self, text: str) -> list[float]:
      """Crée un embedding vectoriel du texte"""
      if not text.strip():
          return [0.0] * settings.azure_openai_embedding_dimensions

      try:
          response = await self.client.embeddings.create(
              model=settings.azure_openai_embedding_deployment,
              input=text,
              dimensions=settings.azure_openai_embedding_dimensions
          )
          return response.data[0].embedding
      except Exception as e:
          print(f"Embedding Error: {e}")
          return [0.0] * settings.azure_openai_embedding_dimensions

  def _labels_to_searchable_text(self, labels) -> str:
      """Convertit les labels (list ou JSON string) en texte pour embedding"""
      if isinstance(labels, str):
          # Si c'est déjà du JSON, essayer de le parser
          try:
              import json
              parsed = json.loads(labels)
              # Extraire le texte searchable
              parts = []
              if isinstance(parsed, dict):
                  if 'searchable_text' in parsed:
                      parts.append(parsed['searchable_text'])
                  if 'game_elements' in parsed:
                      elements = parsed['game_elements']
                      if isinstance(elements, list):
                          parts.append(" ".join(elements))
                  if 'key_concepts' in parsed:
                      concepts = parsed['key_concepts']
                      if isinstance(concepts, list):
                          parts.append(" ".join(concepts))
                  if 'game_actions' in parsed:
                      actions = parsed['game_actions']
                      if isinstance(actions, list):
                          parts.append(" ".join(actions))
              return " ".join(parts)
          except:
              # Si parsing échoue, utiliser le string tel quel
              return labels
      elif isinstance(labels, list):
          # Liste simple de labels
          return " ".join(str(label) for label in labels)
      else:
          return str(labels)

  async def test_connection(self) -> tuple[bool, str]:
      """Teste la connexion au service Azure OpenAI"""
      try:
          if not settings.azure_openai_api_key:
              return False, "Azure OpenAI API key not configured"

          if not settings.azure_openai_endpoint:
              return False, "Azure OpenAI endpoint not configured"

          if not settings.azure_openai_vision_deployment:
              return False, "Azure OpenAI vision deployment not configured"

          # Test simple de connexion avec un appel minimal
          response = await self.client.chat.completions.create(
              model=settings.azure_openai_vision_deployment,
              messages=[{"role": "user", "content": "Test connection"}],
              max_tokens=1
          )
          
          if response:
              return True, "Azure OpenAI connection successful"
          else:
              return False, "No response from Azure OpenAI"

      except Exception as e:
          return False, f"Azure OpenAI connection error: {str(e)}"