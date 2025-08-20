import base64
import json
import os
from pathlib import Path
from typing import Dict, Any

from langchain_openai import AzureChatOpenAI

from app.config import settings
from app.services.interfaces import BaseVisionExtractor


class AzureVisionExtractor(BaseVisionExtractor):
    """Extracteur de règles utilisant Azure OpenAI Vision"""
    
    def __init__(self):
        self.client = AzureChatOpenAI(
            api_version=settings.vision_agent_api_version,
            azure_endpoint=settings.vision_agent_endpoint,
            api_key=os.getenv("SUBSCRIPTION_KEY"),
            deployment_name=settings.vision_agent_deployment
        )
        self.system_prompt = settings.vision_agent_prompt
    
    async def extract_rules_from_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Extrait les règles d'une image de livret en utilisant Azure OpenAI Vision
        
        Args:
            image_path (Path): Chemin vers l'image à analyser
            
        Returns:
            Dict[str, Any]: Données extraites au format JSON
        """
        try:
            # Vérification de l'existence du fichier
            if not image_path.exists():
                return {
                    "status": "error",
                    "message": f"Image non trouvée: {image_path}",
                    "data": None
                }
            
            # Lecture et encodage de l'image en base64
            image_data = self._encode_image(image_path)
            
            # Préparation du message avec l'image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.system_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            # Appel à Azure OpenAI
            response = await self.client.ainvoke(messages)
            
            # Extraction du contenu JSON de la réponse
            content = response.content
            
            # Nettoyage et parsing du JSON
            extracted_data = self._parse_json_response(content)
            
            return {
                "status": "success",
                "message": "Extraction réussie",
                "data": extracted_data,
                "metadata": {
                    "image_path": str(image_path),
                    "image_size": image_path.stat().st_size,
                    "model": settings.vision_agent_deployment
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de l'extraction: {str(e)}",
                "data": None,
                "metadata": {
                    "image_path": str(image_path),
                    "error_type": type(e).__name__
                }
            }
    
    def _encode_image(self, image_path: Path) -> str:
        """Encode une image en base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _parse_json_response(self, response_content: str) -> Dict[str, Any]:
        """Parse et nettoie la réponse JSON du modèle"""
        try:
            # Suppression des éventuels backticks et formatage markdown
            content = response_content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parsing JSON
            parsed_data = json.loads(content)
            
            # Validation de la structure attendue
            expected_keys = ["text_content", "diagrams", "game_elements", "rules", "sections"]
            for key in expected_keys:
                if key not in parsed_data:
                    parsed_data[key] = [] if key != "text_content" else ""
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            # Fallback en cas d'erreur de parsing
            return {
                "text_content": response_content,
                "diagrams": [],
                "game_elements": [],
                "rules": [],
                "sections": [],
                "parse_error": f"JSON parsing error: {str(e)}"
            }