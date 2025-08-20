import json
from typing import Dict, Any, List

from app.services.interfaces import TextChunker


class GameRulesChunker(TextChunker):
    """Chunker spécialisé pour les règles de jeu"""
    
    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Découpe un texte en chunks avec overlap
        
        Args:
            text (str): Texte à découper
            chunk_size (int): Taille maximale des chunks en caractères
            overlap (int): Nombre de caractères de chevauchement
            
        Returns:
            List[str]: Liste des chunks
        """
        if not text or chunk_size <= 0:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Si on n'est pas à la fin, essaie de couper à un espace
            if end < len(text):
                # Recherche du dernier espace dans la zone de coupure
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calcul du prochain début avec overlap
            start = end - overlap if end - overlap > start else end
            
            # Protection contre les boucles infinies
            if start >= len(text):
                break
        
        return chunks
    
    def chunk_json_content(self, json_data: Dict[str, Any], chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """
        Découpe le contenu JSON extrait des images en chunks logiques
        
        Args:
            json_data (Dict[str, Any]): Données extraites d'une image
            chunk_size (int): Taille maximale des chunks
            overlap (int): Overlap en caractères
            
        Returns:
            List[Dict[str, Any]]: Liste des chunks avec métadonnées
        """
        chunks = []
        
        # 1. Chunk du texte principal
        if json_data.get("text_content"):
            text_chunks = self.chunk_text(json_data["text_content"], chunk_size, overlap)
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    "content": chunk,
                    "type": "text_content",
                    "chunk_index": i,
                    "source": "main_text"
                })
        
        # 2. Chunk des règles individuelles
        if json_data.get("rules"):
            for rule_idx, rule in enumerate(json_data["rules"]):
                rule_text = f"Règle: {rule.get('rule', '')}"
                if rule.get('context'):
                    rule_text += f" (Contexte: {rule['context']})"
                
                # Si la règle est trop longue, la découper
                if len(rule_text) > chunk_size:
                    rule_chunks = self.chunk_text(rule_text, chunk_size, overlap)
                    for i, chunk in enumerate(rule_chunks):
                        chunks.append({
                            "content": chunk,
                            "type": "rule",
                            "chunk_index": i,
                            "rule_index": rule_idx,
                            "source": "rules"
                        })
                else:
                    chunks.append({
                        "content": rule_text,
                        "type": "rule",
                        "chunk_index": 0,
                        "rule_index": rule_idx,
                        "source": "rules"
                    })
        
        # 3. Chunk des sections
        if json_data.get("sections"):
            for section_idx, section in enumerate(json_data["sections"]):
                section_text = f"Section {section.get('title', 'Sans titre')} ({section.get('type', 'général')}): {section.get('content', '')}"
                
                if len(section_text) > chunk_size:
                    section_chunks = self.chunk_text(section_text, chunk_size, overlap)
                    for i, chunk in enumerate(section_chunks):
                        chunks.append({
                            "content": chunk,
                            "type": "section",
                            "chunk_index": i,
                            "section_index": section_idx,
                            "section_type": section.get('type', 'général'),
                            "source": "sections"
                        })
                else:
                    chunks.append({
                        "content": section_text,
                        "type": "section",
                        "chunk_index": 0,
                        "section_index": section_idx,
                        "section_type": section.get('type', 'général'),
                        "source": "sections"
                    })
        
        # 4. Chunk des diagrammes et éléments de jeu
        if json_data.get("diagrams"):
            for diag_idx, diagram in enumerate(json_data["diagrams"]):
                diag_text = f"Diagramme {diagram.get('type', 'inconnu')}: {diagram.get('description', '')}"
                chunks.append({
                    "content": diag_text,
                    "type": "diagram",
                    "chunk_index": 0,
                    "diagram_index": diag_idx,
                    "diagram_type": diagram.get('type', 'inconnu'),
                    "source": "diagrams"
                })
        
        # 5. Chunk des éléments de jeu
        if json_data.get("game_elements"):
            elements_text = "Éléments du jeu: " + ", ".join(json_data["game_elements"])
            chunks.append({
                "content": elements_text,
                "type": "game_elements",
                "chunk_index": 0,
                "source": "game_elements"
            })
        
        return chunks
    
    def combine_page_chunks(self, page_chunks: List[List[Dict[str, Any]]], page_metadatas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine les chunks de toutes les pages avec leurs métadonnées
        
        Args:
            page_chunks (List[List[Dict[str, Any]]]): Chunks par page
            page_metadatas (List[Dict[str, Any]]): Métadonnées par page
            
        Returns:
            List[Dict[str, Any]]: Chunks combinés avec métadonnées complètes
        """
        combined_chunks = []
        
        for page_idx, (chunks, page_meta) in enumerate(zip(page_chunks, page_metadatas)):
            for chunk in chunks:
                # Enrichissement avec les métadonnées de page
                enriched_chunk = {
                    **chunk,
                    "page_index": page_idx,
                    "page_path": page_meta.get("image_path", ""),
                    "extraction_status": page_meta.get("status", "unknown")
                }
                combined_chunks.append(enriched_chunk)
        
        return combined_chunks