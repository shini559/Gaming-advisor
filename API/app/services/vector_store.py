import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.services.interfaces import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    """Implementation du vector store utilisant ChromaDB"""
    
    def __init__(self):
        # Création du dossier de stockage
        self.store_path = Path(settings.vector_store_dir)
        self.store_path.mkdir(exist_ok=True)
        
        # Initialisation du client ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.store_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    async def create_collection(self, collection_name: str) -> bool:
        """
        Crée une nouvelle collection pour un jeu
        
        Args:
            collection_name (str): Nom de la collection (généralement game_id)
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Supprime la collection si elle existe déjà
            try:
                self.client.delete_collection(name=collection_name)
            except ValueError:
                # Collection n'existe pas, c'est normal
                pass
            
            # Crée la nouvelle collection
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création de la collection {collection_name}: {str(e)}")
            return False
    
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        embeddings: List[List[float]], 
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Ajoute des documents à une collection
        
        Args:
            collection_name (str): Nom de la collection
            documents (List[str]): Liste des documents texte
            embeddings (List[List[float]]): Liste des embeddings correspondants
            metadatas (Optional[List[Dict[str, Any]]]): Métadonnées optionnelles
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            if len(documents) != len(embeddings):
                print("Erreur: nombre de documents != nombre d'embeddings")
                return False
            
            # Récupération de la collection
            collection = self.client.get_collection(name=collection_name)
            
            # Génération d'IDs uniques pour chaque document
            ids = [str(uuid.uuid4()) for _ in documents]
            
            # Préparation des métadonnées si non fournies
            if metadatas is None:
                metadatas = [{"index": i} for i in range(len(documents))]
            elif len(metadatas) != len(documents):
                # Complétion des métadonnées manquantes
                while len(metadatas) < len(documents):
                    metadatas.append({"index": len(metadatas)})
            
            # Ajout des documents à la collection
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de documents à {collection_name}: {str(e)}")
            return False
    
    async def search(
        self, 
        collection_name: str, 
        query_embedding: List[float], 
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Recherche des documents similaires dans une collection
        
        Args:
            collection_name (str): Nom de la collection
            query_embedding (List[float]): Embedding de la requête
            n_results (int): Nombre de résultats à retourner
            
        Returns:
            Dict[str, Any]: Résultats de la recherche
        """
        try:
            # Récupération de la collection
            collection = self.client.get_collection(name=collection_name)
            
            # Recherche vectorielle
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, collection.count()),
                include=['documents', 'metadatas', 'distances']
            )
            
            # Formatage des résultats
            formatted_results = {
                "documents": results['documents'][0] if results['documents'] else [],
                "metadatas": results['metadatas'][0] if results['metadatas'] else [],
                "distances": results['distances'][0] if results['distances'] else [],
                "total_found": len(results['documents'][0]) if results['documents'] else 0
            }
            
            return formatted_results
            
        except Exception as e:
            print(f"Erreur lors de la recherche dans {collection_name}: {str(e)}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "total_found": 0,
                "error": str(e)
            }
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Supprime une collection
        
        Args:
            collection_name (str): Nom de la collection à supprimer
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            self.client.delete_collection(name=collection_name)
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de {collection_name}: {str(e)}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Récupère les informations d'une collection
        
        Args:
            collection_name (str): Nom de la collection
            
        Returns:
            Dict[str, Any]: Informations de la collection
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        except Exception as e:
            return {
                "name": collection_name,
                "count": 0,
                "metadata": {},
                "error": str(e)
            }
    
    def list_collections(self) -> List[str]:
        """
        Liste toutes les collections disponibles
        
        Returns:
            List[str]: Liste des noms de collections
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            print(f"Erreur lors de la liste des collections: {str(e)}")
            return []