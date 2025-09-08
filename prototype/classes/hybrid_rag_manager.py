import os
import json
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage

from classes.image_store_manager import ImageStoreManager


class HybridRAGManager:
    """RAG Hybride : métadonnées en ChromaDB + images directes à l'agent"""
    
    def __init__(self, settings, game_name=None):
        print("🚀 RAG Hybride: Initialisation")
        self.settings = settings
        self.game_name = game_name or "default"
        
        # Configuration embeddings - utiliser celui des settings hybride s'il existe
        if hasattr(settings, 'hybrid_embedding_model') and settings.hybrid_embedding_model:
            try:
                self.embeddings = settings.hybrid_embedding_model
                print("✅ RAG Hybride: Utilisation du modèle d'embedding hybride depuis settings")
            except Exception as e:
                print(f"⚠️ RAG Hybride: Erreur modèle embedding settings: {e}")
                self.embeddings = None
        else:
            # Fallback vers configuration environnement
            embeddings_deployment = os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT_NAME")
            
            if embeddings_deployment:
                try:
                    self.embeddings = AzureOpenAIEmbeddings(
                        api_version="2024-12-01-preview",
                        azure_endpoint="https://gameadvisorai.openai.azure.com/",
                        api_key=os.getenv("SUBSCRIPTION_KEY"),
                        deployment=embeddings_deployment
                    )
                    print("✅ RAG Hybride: Embeddings Azure configurés (fallback)")
                except Exception as e:
                    print(f"⚠️ RAG Hybride: Erreur embeddings: {e}")
                    self.embeddings = None
            else:
                print("⚠️ RAG Hybride: Pas de déploiement embeddings configuré")
                self.embeddings = None
        
        # Configuration ChromaDB pour métadonnées (collection séparée)
        persist_dir = settings.params.get("chroma_persist_directory", "./chroma_db")
        
        if self.embeddings:
            try:
                collection_name = f"hybrid_metadata_{self.game_name}"
                self.vector_store = Chroma(
                    collection_name=collection_name,
                    persist_directory=persist_dir,
                    embedding_function=self.embeddings
                )
                print(f"✅ RAG Hybride: ChromaDB configuré pour métadonnées ({persist_dir}/{collection_name})")
            except Exception as e:
                print(f"⚠️ RAG Hybride: Erreur ChromaDB: {e}")
                self.vector_store = None
        else:
            self.vector_store = None
        
        # Gestionnaire d'images avec nom du jeu
        self.image_store = ImageStoreManager(game_name=self.game_name)
        
        # Modèles hybride spécifiques
        self.vision_model = settings.hybrid_vision_model
        # Utiliser l'agent principal pour toutes les méthodes
        self.agent_model = settings.agent_model
        
        # Fallback simulation
        self.analyzed_documents = []
    
    def process_game_document(self, images_data):
        """Traite un document : analyse vision + stockage hybride"""
        total_vision_tokens = 0
        total_embedding_tokens = 0
        
        print(f"🔄 RAG Hybride: Traitement de {len(images_data)} images")
        
        # 1. Analyser chaque image et stocker
        stored_image_ids = []
        for img in images_data:
            # Analyse vision pour métadonnées (réutilise code existant)
            page_analysis, vision_tokens = self._analyze_page(img)
            total_vision_tokens += vision_tokens
            
            # Stocker image + métadonnées localement
            if isinstance(page_analysis, str):
                try:
                    metadata = json.loads(page_analysis)
                except:
                    metadata = {"raw_analysis": page_analysis}
            else:
                metadata = page_analysis
            
            image_id = self.image_store.store_image(img, metadata, "game_rules")
            stored_image_ids.append(image_id)
        
        # 2. Créer embeddings des métadonnées et stocker dans ChromaDB
        embedding_tokens = self._store_metadata_in_vector_db(stored_image_ids)
        total_embedding_tokens += embedding_tokens
        
        # 3. Rapport final
        total_tokens = total_vision_tokens + total_embedding_tokens
        print(f"📊 RAG HYBRIDE TOKENS: Vision={total_vision_tokens}, Embeddings={total_embedding_tokens}, Total={total_tokens}")
        print(f"📷 RAG Hybride: {len(stored_image_ids)} images stockées")
        
        return {
            "vision_tokens": total_vision_tokens,
            "embedding_tokens": total_embedding_tokens,
            "total_tokens": total_tokens,
            "stored_images": len(stored_image_ids)
        }
    
    def _analyze_page(self, image_data):
        """Analyse vision d'une page (réutilise logique RAGManager)"""
        print(f"📄 RAG Hybride: Analyse de {image_data.get('name', 'image')}")
        
        # Essayer analyse vision réelle
        if self.vision_model:
            try:
                prompt = self.settings.hybrid_vision_prompt

                message = HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data['data']}"}
                    }
                ])
                
                # Estimation tokens
                prompt_tokens = len(prompt) // 4
                image_tokens = self._estimate_image_tokens(image_data['data'])
                estimated_input_tokens = prompt_tokens + image_tokens
                
                response = self.vision_model.invoke([message])
                
                output_tokens = len(response.content) // 4
                total_vision_tokens = estimated_input_tokens + output_tokens
                
                print(f"✅ RAG Hybride: Métadonnées extraites ({len(response.content)} chars)")
                print(f"💰 Vision tokens: ≈{total_vision_tokens}")
                
                return response.content, total_vision_tokens
                
            except Exception as e:
                print(f"❌ RAG Hybride: Erreur analyse vision: {e}")
                # Fallback simulation
                pass
        
        # Simulation si vision non disponible
        simulated_metadata = {
            "game_elements": ["cartes", "jetons", "plateau"],
            "diagrams": [{"type": "tableau", "description": "Tableau de scores", "elements": ["points", "victoire"]}],
            "game_actions": ["placer", "déplacer", "piocher"],
            "key_concepts": ["points", "tours", "victoire"],
            "sections": [{"title": "Setup", "type": "setup", "keywords": ["mise en place", "préparation"]}],
            "searchable_text": f"Métadonnées simulées pour {image_data.get('name', 'image')}"
        }
        
        print(f"⚠️ RAG Hybride: Métadonnées simulées")
        return simulated_metadata, 0
    
    def _estimate_image_tokens(self, base64_data):
        """Estimation tokens image (réutilise logique existante)"""
        image_size_bytes = len(base64_data) * 3 // 4
        
        if image_size_bytes < 50000:
            return 85
        elif image_size_bytes < 200000:
            return 170
        else:
            return 255
    
    def _store_metadata_in_vector_db(self, image_ids):
        """Stocke les métadonnées dans ChromaDB avec références aux images"""
        print(f"💾 RAG Hybride: Vectorisation métadonnées pour {len(image_ids)} images")
        
        if self.vector_store:
            try:
                documents = []
                metadatas = []
                
                for image_id in image_ids:
                    # Récupérer métadonnées de l'image
                    image_data = self.image_store.get_image(image_id)
                    if not image_data:
                        continue
                    
                    metadata = image_data['metadata']
                    
                    # DEBUG: Examiner les métadonnées brutes
                    print(f"🔍 METADATA DEBUG: Keys = {list(metadata.keys())}")
                    if isinstance(metadata, dict):
                        for key, value in metadata.items():
                            print(f"   {key}: {type(value)} = '{str(value)[:100]}...'")
                    
                    # Créer texte searchable à partir des métadonnées
                    searchable_parts = []
                    
                    # Vérifier si les métadonnées sont du JSON mal parsé
                    if 'raw_analysis' in metadata and isinstance(metadata.get('raw_analysis'), str):
                        raw_text = metadata['raw_analysis']
                        
                        # Nettoyer le JSON des blocs markdown
                        if raw_text.startswith('```json'):
                            # Supprimer ```json au début et ``` à la fin
                            json_start = raw_text.find('\n') + 1
                            json_end = raw_text.rfind('\n```')
                            if json_end == -1:
                                json_end = raw_text.rfind('```')
                            if json_end != -1:
                                clean_json = raw_text[json_start:json_end].strip()
                            else:
                                clean_json = raw_text[json_start:].strip()
                        elif raw_text.startswith('```'):
                            # Format ```\n{json}\n```
                            json_start = raw_text.find('\n') + 1
                            json_end = raw_text.rfind('\n```')
                            if json_end == -1:
                                json_end = raw_text.rfind('```')
                            if json_end != -1:
                                clean_json = raw_text[json_start:json_end].strip()
                            else:
                                clean_json = raw_text[json_start:].strip()
                        else:
                            clean_json = raw_text.strip()
                        
                        print(f"🧹 JSON nettoyé ({len(clean_json)} chars): '{clean_json[:80]}...'")
                        
                        # Essayer de parser le JSON nettoyé
                        try:
                            import json
                            parsed_metadata = json.loads(clean_json)
                            print(f"🔧 JSON parsé avec succès: {list(parsed_metadata.keys())}")
                            # Remplacer metadata par les données parsées
                            metadata.update(parsed_metadata)
                        except json.JSONDecodeError as e:
                            print(f"❌ Erreur parsing JSON nettoyé: {e}")
                            print(f"   Contenu JSON: '{clean_json[:200]}...'")
                            # Fallback : utiliser le texte brut
                            metadata['searchable_text'] = clean_json
                    
                    if 'searchable_text' in metadata:
                        searchable_parts.append(str(metadata['searchable_text']))
                    
                    if 'game_elements' in metadata and metadata['game_elements']:
                        elements = metadata['game_elements']
                        if isinstance(elements, list):
                            searchable_parts.append("Éléments: " + ", ".join(elements))
                        elif isinstance(elements, str):
                            searchable_parts.append("Éléments: " + elements)
                    
                    if 'key_concepts' in metadata and metadata['key_concepts']:
                        concepts = metadata['key_concepts']
                        if isinstance(concepts, list):
                            searchable_parts.append("Concepts: " + ", ".join(concepts))
                        elif isinstance(concepts, str):
                            searchable_parts.append("Concepts: " + concepts)
                    
                    if 'game_actions' in metadata and metadata['game_actions']:
                        actions = metadata['game_actions']
                        if isinstance(actions, list):
                            searchable_parts.append("Actions: " + ", ".join(actions))
                        elif isinstance(actions, str):
                            searchable_parts.append("Actions: " + actions)
                    
                    if 'sections' in metadata and metadata['sections']:
                        sections = metadata['sections']
                        if isinstance(sections, list):
                            for section in sections:
                                if isinstance(section, dict) and 'keywords' in section and section['keywords']:
                                    keywords = section['keywords']
                                    if isinstance(keywords, list):
                                        searchable_parts.append("Section: " + ", ".join(keywords))
                                    elif isinstance(keywords, str):
                                        searchable_parts.append("Section: " + keywords)
                    
                    searchable_text = " | ".join(searchable_parts)
                    
                    # DEBUG: Logs détaillés pendant l'indexation
                    print(f"🔍 INDEXATION: Image {image_id}")
                    print(f"   📝 Texte searchable ({len(searchable_text)} chars): '{searchable_text[:120]}...'")
                    print(f"   📁 Original: {image_data.get('original_name', 'N/A')}")
                    if 'searchable_text' in metadata:
                        print(f"   🎯 Searchable direct: '{metadata['searchable_text'][:80]}...'")
                    
                    documents.append(searchable_text)
                    
                    # Métadonnées pour ChromaDB (avec référence image)
                    chroma_metadata = {
                        "image_id": image_id,
                        "image_path": image_data['image_path'],
                        "source": "hybrid_rag",
                        "game": self.game_name,
                        **{k: str(v) for k, v in metadata.items() if k not in ['image_id', 'image_path', 'stored_at']}
                    }
                    metadatas.append(chroma_metadata)
                
                # Estimation tokens embeddings
                total_chars = sum(len(doc) for doc in documents)
                estimated_embedding_tokens = total_chars // 4
                
                # DEBUG: Vérification unicité avant stockage
                unique_docs = set(documents)
                print(f"🔍 INDEXATION FINAL: {len(documents)} documents, {len(unique_docs)} uniques")
                if len(unique_docs) < len(documents):
                    print(f"⚠️ PROBLÈME: {len(documents) - len(unique_docs)} documents dupliqués détectés !")
                    for i, doc in enumerate(documents):
                        print(f"   Doc {i+1}: '{doc[:60]}...'")
                else:
                    print("✅ Tous les documents à indexer sont uniques")
                
                # Ajouter au vector store
                self.vector_store.add_texts(
                    texts=documents,
                    metadatas=metadatas
                )
                
                print(f"✅ RAG Hybride: {len(documents)} métadonnées vectorisées")
                print(f"💰 Embeddings tokens: ≈{estimated_embedding_tokens}")
                
                return estimated_embedding_tokens
                
            except Exception as e:
                print(f"❌ RAG Hybride: Erreur vectorisation: {e}")
                self._store_simulation(image_ids)
                return 0
        else:
            self._store_simulation(image_ids)
            return 0
    
    def retrieve_relevant_images(self, user_query, k=3):
        """Recherche images pertinentes et retourne images directes + contexte"""
        print(f"🔎 RAG Hybride: Recherche pour '{user_query[:50]}...'")
        print(f"🔍 DEBUG: Query complète = '{user_query}'")
        
        if self.embeddings and self.vector_store:
            try:
                # Vérifier le nombre total de documents dans la collection
                collection_count = self.vector_store._collection.count()
                print(f"🔍 DEBUG: Collection contient {collection_count} documents au total")
                
                # SOLUTION CACHE: Forcer la recréation du vector store pour contourner le cache LangChain
                print("🔧 DEBUG: Force refresh du vector store pour éviter le cache")
                persist_dir = self.settings.params.get("chroma_persist_directory", "./chroma_db")
                
                # Recréer le vector store avec les mêmes paramètres pour éviter le cache
                collection_name = f"hybrid_metadata_{self.game_name}"
                fresh_vector_store = Chroma(
                    collection_name=collection_name,
                    persist_directory=persist_dir,
                    embedding_function=self.embeddings
                )
                
                # DIAGNOSTIC: Vérifier l'embedding de la query
                print(f"🔍 DEBUG: Test embedding de la query")
                try:
                    query_embedding = self.embeddings.embed_query(user_query)
                    print(f"🔍 DEBUG: Query embedding généré: {len(query_embedding)} dimensions, début: {query_embedding[:3]}")
                except Exception as e:
                    print(f"❌ DEBUG: Erreur génération query embedding: {e}")
                
                # DIAGNOSTIC: Vérifier le contenu de la collection
                print(f"🔍 DEBUG: Vérification contenu collection")
                try:
                    collection = fresh_vector_store._collection
                    all_docs = collection.get(limit=10)  # Récupérer plus de docs
                    print(f"🔍 DEBUG: Collection a {len(all_docs['ids'])} documents")
                    
                    # Vérifier si tous les textes sont identiques
                    unique_texts = set()
                    for i, (doc_id, doc_text, metadata) in enumerate(zip(all_docs['ids'][:5], all_docs['documents'][:5], all_docs['metadatas'][:5])):
                        print(f"🔍 DEBUG: Doc {i+1}: ID={doc_id}")
                        print(f"   📝 Texte ({len(doc_text)} chars): '{doc_text[:100]}...'")
                        print(f"   🏷️ Image ID: {metadata.get('image_id', 'N/A')}")
                        unique_texts.add(doc_text)
                    
                    print(f"🔍 DEBUG: Nombre de textes uniques: {len(unique_texts)} / {len(all_docs['documents'][:5])}")
                    
                    if len(unique_texts) == 1:
                        print("❌ PROBLÈME IDENTIFIÉ: Tous les documents ont le même contenu textuel !")
                        print(f"   📝 Contenu répété: '{list(unique_texts)[0][:150]}...'")
                    elif len(unique_texts) < len(all_docs['documents'][:5]):
                        print(f"⚠️ PROBLÈME PARTIEL: Seulement {len(unique_texts)} textes uniques sur {len(all_docs['documents'][:5])}")
                    else:
                        print("✅ Les documents ont des contenus différents")
                        
                except Exception as e:
                    print(f"❌ DEBUG: Erreur lecture collection: {e}")
                
                # Test SANS filtre d'abord pour voir si c'est le filtre qui pose problème
                print(f"🔍 DEBUG: Test similarity search SANS filtre")
                similar_chunks_no_filter = fresh_vector_store.similarity_search_with_score(
                    user_query,
                    k=k
                )
                print(f"🔍 DEBUG: Sans filtre: {len(similar_chunks_no_filter) if similar_chunks_no_filter else 0} chunks")
                if similar_chunks_no_filter:
                    for i, (chunk, score) in enumerate(similar_chunks_no_filter[:3], 1):
                        print(f"🔍 DEBUG: Sans filtre Chunk {i} - Score: {score:.4f} - Source: {chunk.metadata.get('source', 'N/A')}")
                
                # Recherche par similarité dans les métadonnées avec scores sur le store fraîchement créé
                print(f"🔍 DEBUG: Appel similarity_search_with_score avec k={k} sur fresh store AVEC filtre")
                similar_chunks_with_scores = fresh_vector_store.similarity_search_with_score(
                    user_query,
                    k=k,  # Nombre d'images à récupérer
                    filter={"$and": [{"source": {"$eq": "hybrid_rag"}}, {"game": {"$eq": self.game_name}}]}
                )
                print(f"🔍 DEBUG: similarity_search_with_score retourné {len(similar_chunks_with_scores) if similar_chunks_with_scores else 0} chunks")
                
                # Extraire les chunks et afficher les scores
                similar_chunks = []
                if similar_chunks_with_scores:
                    for i, (chunk, score) in enumerate(similar_chunks_with_scores, 1):
                        similar_chunks.append(chunk)
                        print(f"🔍 DEBUG: Chunk {i} - Score: {score:.4f} - ID: {chunk.metadata.get('image_id', 'inconnu')}")
                
                if similar_chunks:
                    # Extraire les image_ids des résultats
                    image_ids = [chunk.metadata.get('image_id') for chunk in similar_chunks if 'image_id' in chunk.metadata]
                    
                    # Logs détaillés des images trouvées
                    print(f"✅ RAG Hybride: {len(similar_chunks)} métadonnées trouvées")
                    for i, chunk in enumerate(similar_chunks, 1):
                        metadata = chunk.metadata
                        image_id = metadata.get('image_id', 'inconnu')
                        
                        log_info = f"🖼️ Image {i}: {image_id}"
                        if 'image_path' in metadata:
                            filename = os.path.basename(metadata['image_path'])
                            log_info += f" ({filename})"
                        
                        print(log_info)
                        
                        # Afficher les éléments de jeu détectés
                        if 'game_elements' in metadata:
                            elements_str = metadata['game_elements']
                            if isinstance(elements_str, str) and elements_str.startswith('['):
                                try:
                                    import ast
                                    elements = ast.literal_eval(elements_str)
                                    print(f"   🎮 Éléments: {', '.join(elements[:5])}{'...' if len(elements) > 5 else ''}")
                                except:
                                    print(f"   🎮 Éléments: {elements_str[:50]}...")
                            else:
                                print(f"   🎮 Éléments: {str(elements_str)[:50]}...")
                        
                        # Afficher les concepts clés
                        if 'key_concepts' in metadata:
                            concepts_str = metadata['key_concepts']
                            if isinstance(concepts_str, str) and concepts_str.startswith('['):
                                try:
                                    import ast
                                    concepts = ast.literal_eval(concepts_str)
                                    print(f"   💡 Concepts: {', '.join(concepts[:5])}{'...' if len(concepts) > 5 else ''}")
                                except:
                                    print(f"   💡 Concepts: {concepts_str[:50]}...")
                            else:
                                print(f"   💡 Concepts: {str(concepts_str)[:50]}...")
                        
                        # Aperçu du texte de recherche
                        searchable_preview = chunk.page_content[:80] + "..." if len(chunk.page_content) > 80 else chunk.page_content
                        print(f"   💬 Contexte: {searchable_preview}")
                    
                    # Récupérer les images complètes
                    images = self.image_store.get_images_by_ids(image_ids)
                    
                    # Logs des images effectivement récupérées
                    if images:
                        print(f"📷 RAG Hybride: {len(images)} images chargées pour l'agent")
                        for i, img in enumerate(images, 1):
                            original_name = img['metadata'].get('original_name', 'inconnu')
                            image_size = len(img['image_data']) // 1024  # Taille approximative en KB
                            print(f"   📄 Image {i}: {original_name} (~{image_size}KB)")
                    
                    # Formater le contexte hybride
                    context = self._format_hybrid_context(images, similar_chunks)
                    
                    return {
                        "images": images,  # Images directes pour l'agent
                        "context": context,  # Contexte textuel
                        "image_count": len(images)
                    }
                else:
                    print("⚠️ RAG Hybride: Aucune image pertinente trouvée")
                    return None
                    
            except Exception as e:
                print(f"❌ RAG Hybride: Erreur recherche: {e}")
                return None
        else:
            print("⚠️ RAG Hybride: Composants non configurés")
            return {"context": f"[Simulation hybride pour: {user_query[:30]}...]", "images": [], "image_count": 0}
    
    def _format_hybrid_context(self, images, chunks):
        """Formate le contexte hybride (métadonnées + références images)"""
        if not images or not chunks:
            return None
        
        context_parts = []
        for i, (image, chunk) in enumerate(zip(images, chunks), 1):
            metadata = image['metadata']
            
            context_part = f"[Image {i}] {metadata.get('original_name', 'image')}:\n"
            
            if 'game_elements' in metadata:
                context_part += f"  • Éléments: {', '.join(metadata['game_elements'])}\n"
            
            if 'key_concepts' in metadata:
                context_part += f"  • Concepts: {', '.join(metadata['key_concepts'])}\n"
            
            if 'sections' in metadata and metadata['sections']:
                section_types = [s.get('type', 'général') for s in metadata['sections']]
                context_part += f"  • Sections: {', '.join(set(section_types))}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _store_simulation(self, image_ids):
        """Stockage simulation"""
        for image_id in image_ids:
            self.analyzed_documents.append({
                "image_id": image_id,
                "content": f"[Métadonnées simulées pour {image_id}]",
                "timestamp": "now"
            })
        print(f"📚 RAG Hybride: {len(self.analyzed_documents)} images en simulation")
    
    def clear_vector_store(self):
        """Vide le store hybride (métadonnées + images)"""
        if self.vector_store:
            try:
                collection = self.vector_store._collection
                all_docs = collection.get()
                
                if all_docs['ids']:
                    collection.delete(ids=all_docs['ids'])
                    print(f"🗑️ RAG Hybride: {len(all_docs['ids'])} métadonnées supprimées")
                else:
                    print("🗑️ RAG Hybride: Store métadonnées déjà vide")
                
                # Vider aussi les images stockées
                self.image_store.clear_storage("game_rules")
                
                # Vider simulation
                self.analyzed_documents = []
                
            except Exception as e:
                print(f"❌ RAG Hybride: Erreur vidage: {e}")
                raise e
        else:
            print("⚠️ RAG Hybride: Pas de store à vider")
    
    def get_vector_store_info(self):
        """Infos sur le store hybride"""
        if self.vector_store:
            try:
                collection = self.vector_store._collection
                metadata_count = collection.count()
                
                image_info = self.image_store.get_storage_info()
                
                return {
                    "document_count": metadata_count,
                    "image_count": image_info["total_images"],
                    "store_type": "Hybrid (ChromaDB + Images)",
                    "has_documents": metadata_count > 0,
                    "storage_info": image_info
                }
            except:
                return {
                    "document_count": 0,
                    "image_count": 0,
                    "store_type": "Hybrid (ChromaDB + Images)",
                    "has_documents": False
                }
        else:
            image_info = self.image_store.get_storage_info()
            return {
                "document_count": len(self.analyzed_documents),
                "image_count": image_info["total_images"],
                "store_type": "Simulation Hybride",
                "has_documents": len(self.analyzed_documents) > 0,
                "storage_info": image_info
            }