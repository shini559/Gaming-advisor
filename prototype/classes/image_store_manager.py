import os
import hashlib
import base64
from typing import Dict, List, Optional
from pathlib import Path
import json


class ImageStoreManager:
    """Gestionnaire de stockage local d'images pour le RAG hybride"""
    
    def __init__(self, storage_dir: str = "./stored_images", game_name: str = None):
        self.storage_dir = Path(storage_dir)
        self.game_name = game_name or "default"
        
        # Créer dossier spécifique au jeu
        self.game_dir = self.storage_dir / self.game_name
        self.game_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer dossiers par type sous le dossier du jeu
        (self.game_dir / "game_rules").mkdir(exist_ok=True)
        (self.game_dir / "metadata").mkdir(exist_ok=True)
        
        print(f"📁 ImageStore: Dossier configuré pour {self.game_name} ({self.game_dir})")
    
    def store_image(self, image_data: Dict, metadata: Dict, source_type: str = "game_rules") -> str:
        """
        Stocke une image avec ses métadonnées
        
        Args:
            image_data: Dict avec 'data' (base64) et 'name'
            metadata: Métadonnées extraites par l'IA
            source_type: Type de source (game_rules, question, etc.)
            
        Returns:
            image_id: ID unique de l'image stockée
        """
        # Générer ID unique basé sur le contenu
        content_hash = hashlib.md5(image_data['data'].encode()).hexdigest()[:12]
        image_id = f"{source_type}_{content_hash}"
        
        # Chemins de stockage dans le dossier du jeu
        image_path = self.game_dir / source_type / f"{image_id}.png"
        metadata_path = self.game_dir / "metadata" / f"{image_id}.json"
        
        try:
            # Sauvegarder image
            image_bytes = base64.b64decode(image_data['data'])
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            # Sauvegarder métadonnées enrichies
            enriched_metadata = {
                **metadata,
                "image_id": image_id,
                "original_name": image_data.get('name', 'unknown'),
                "image_path": str(image_path),
                "source_type": source_type,
                "stored_at": "now"  # Simplifié pour l'exemple
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_metadata, f, ensure_ascii=False, indent=2)
            
            print(f"💾 ImageStore: Image {image_id} stockée")
            return image_id
            
        except Exception as e:
            print(f"❌ ImageStore: Erreur stockage {image_id}: {e}")
            raise e
    
    def get_image(self, image_id: str) -> Optional[Dict]:
        """
        Récupère une image et ses métadonnées par ID
        
        Returns:
            Dict avec 'image_data' (base64), 'metadata', 'image_path'
        """
        try:
            # Trouver l'image dans les différents dossiers du jeu
            image_path = None
            for subdir in self.game_dir.iterdir():
                if subdir.is_dir() and subdir.name != "metadata":
                    potential_path = subdir / f"{image_id}.png"
                    if potential_path.exists():
                        image_path = potential_path
                        break
            
            if not image_path or not image_path.exists():
                print(f"⚠️ ImageStore: Image {image_id} non trouvée")
                return None
            
            # Charger métadonnées
            metadata_path = self.game_dir / "metadata" / f"{image_id}.json"
            if not metadata_path.exists():
                print(f"⚠️ ImageStore: Métadonnées {image_id} non trouvées")
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Charger image en base64
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode()
            
            return {
                "image_data": image_base64,
                "metadata": metadata,
                "image_path": str(image_path),
                "image_id": image_id
            }
            
        except Exception as e:
            print(f"❌ ImageStore: Erreur récupération {image_id}: {e}")
            return None
    
    def get_images_by_ids(self, image_ids: List[str]) -> List[Dict]:
        """Récupère plusieurs images par leurs IDs"""
        images = []
        for image_id in image_ids:
            image_data = self.get_image(image_id)
            if image_data:
                images.append(image_data)
        
        print(f"📷 ImageStore: {len(images)}/{len(image_ids)} images récupérées")
        return images
    
    def search_images_by_metadata(self, query_terms: List[str], source_type: str = "game_rules") -> List[str]:
        """
        Recherche basique dans les métadonnées (sera remplacée par ChromaDB)
        
        Returns:
            List des image_ids correspondants
        """
        matching_ids = []
        metadata_dir = self.game_dir / "metadata"
        
        try:
            for metadata_file in metadata_dir.glob("*.json"):
                if not metadata_file.name.startswith(source_type):
                    continue
                    
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Recherche simple par mots-clés
                metadata_text = json.dumps(metadata, ensure_ascii=False).lower()
                if any(term.lower() in metadata_text for term in query_terms):
                    image_id = metadata_file.stem
                    matching_ids.append(image_id)
            
            print(f"🔍 ImageStore: {len(matching_ids)} images trouvées pour {query_terms}")
            return matching_ids
            
        except Exception as e:
            print(f"❌ ImageStore: Erreur recherche: {e}")
            return []
    
    def clear_storage(self, source_type: Optional[str] = None):
        """Vide le stockage (tout ou par type)"""
        try:
            if source_type:
                # Vider un type spécifique
                source_dir = self.game_dir / source_type
                if source_dir.exists():
                    for file in source_dir.glob("*"):
                        file.unlink()
                    print(f"🗑️ ImageStore: {source_type} vidé pour {self.game_name}")
            else:
                # Vider tout le jeu
                for subdir in self.game_dir.iterdir():
                    if subdir.is_dir():
                        for file in subdir.glob("*"):
                            file.unlink()
                print(f"🗑️ ImageStore: Stockage vidé pour {self.game_name}")
                
        except Exception as e:
            print(f"❌ ImageStore: Erreur vidage: {e}")
            raise e
    
    def get_storage_info(self) -> Dict:
        """Retourne des infos sur le stockage"""
        try:
            info = {
                "total_images": 0,
                "by_type": {},
                "storage_path": str(self.game_dir),
                "game_name": self.game_name
            }
            
            for subdir in self.game_dir.iterdir():
                if subdir.is_dir() and subdir.name != "metadata":
                    count = len(list(subdir.glob("*.png")))
                    info["by_type"][subdir.name] = count
                    info["total_images"] += count
            
            return info
            
        except Exception as e:
            print(f"❌ ImageStore: Erreur info storage: {e}")
            return {"total_images": 0, "by_type": {}, "storage_path": str(self.game_dir), "game_name": self.game_name}