import base64
from io import BytesIO
from typing import BinaryIO, Optional
import asyncio

from openai import AsyncAzureOpenAI
from PIL import Image

from app.config import settings
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

          # Traitement en parallèle des 3 tâches
          ocr_task = self._extract_text(image_base64)
          description_task = self._describe_image(image_base64)
          labels_task = self._label_image(image_base64)

          # Attendre tous les résultats
          extracted_text, visual_description, labels = await asyncio.gather(
              ocr_task, description_task, labels_task
          )

          # Vectorisation en parallèle du texte et de la description
          text_embedding_task = self._create_embedding(extracted_text)
          desc_embedding_task = self._create_embedding(visual_description)

          text_embedding, description_embedding = await asyncio.gather(
              text_embedding_task, desc_embedding_task
          )

          return AIProcessingResult(
              extracted_text=extracted_text,
              visual_description=visual_description,
              labels=labels,
              text_embedding=text_embedding,
              description_embedding=description_embedding,
              success=True
          )

      except Exception as e:
          return AIProcessingResult(
              extracted_text="",
              visual_description="",
              labels=[],
              text_embedding=[],
              description_embedding=[],
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