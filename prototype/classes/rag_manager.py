import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage


class RAGManager:
    def __init__(self, settings):
        print("🚀 RAG: Initialisation")
        
        # Configuration embeddings Azure
        embeddings_deployment = os.getenv("AZURE_EMBEDDINGS_DEPLOYMENT_NAME")
        
        if embeddings_deployment:
            try:
                self.embeddings = AzureOpenAIEmbeddings(
                    api_version="2024-12-01-preview",
                    azure_endpoint="https://gameadvisorai.openai.azure.com/",
                    api_key=os.getenv("SUBSCRIPTION_KEY"),
                    deployment=embeddings_deployment
                )
                print("✅ RAG: Embeddings Azure configurés")
            except Exception as e:
                print(f"⚠️ RAG: Erreur embeddings: {e}")
                self.embeddings = None
        else:
            print("⚠️ RAG: Pas de déploiement embeddings configuré")
            self.embeddings = None
            
        # Configuration ChromaDB
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        
        if self.embeddings:
            try:
                self.vector_store = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=self.embeddings
                )
                print(f"✅ RAG: ChromaDB configuré ({persist_dir})")
            except Exception as e:
                print(f"⚠️ RAG: Erreur ChromaDB: {e}")
                self.vector_store = None
        else:
            self.vector_store = None
            
        self.vision_model = settings.rag_vision_model
        
        # Fallback simulation si pas de RAG réel
        self.analyzed_documents = []

    def process_game_document(self, images_data):
        """Traite un document de jeu complet"""
        total_vision_tokens = 0
        total_embedding_tokens = 0
        
        # 1. Extraire text + schémas de chaque page
        extracted_data = []
        for img in images_data:
            page_analysis, vision_tokens = self._analyze_page(img)
            extracted_data.append(page_analysis)
            total_vision_tokens += vision_tokens

        # 2. Créer embeddings et stocker
        embedding_tokens = self._store_in_vector_db(extracted_data)
        total_embedding_tokens += embedding_tokens
        
        # 3. Rapport final des tokens
        total_tokens = total_vision_tokens + total_embedding_tokens
        print(f"📊 RAG TOKENS: Vision={total_vision_tokens}, Embeddings={total_embedding_tokens}, Total={total_tokens}")
        
        return {
            "vision_tokens": total_vision_tokens,
            "embedding_tokens": total_embedding_tokens, 
            "total_tokens": total_tokens
        }

    def _analyze_page(self, image_data):
        """Analyse une page avec vision model"""
        print(f"📄 RAG: Analyse de page - {image_data.get('name', 'image')}")
        
        # Essayer analyse vision réelle si modèle disponible
        if self.vision_model:
            try:
                prompt = """Analyse cette page de règles de jeu:

1. TEXTE: Extrait tout le texte visible
2. SCHÉMAS: Décris précisément tous diagrammes, tableaux, illustrations
3. ÉLÉMENTS: Identifie et décris précisemment les composants (cartes, pions, dés, plateau, etc.)
4. RÈGLES: Extrait les règles et mécaniques spécifiques
5. SECTIONS: Catégorise (setup/mise en place, tour de jeu, scoring/points, fin de partie)

Format ta réponse en JSON:
{
    "text_content": "texte intégral visible",
    "diagrams": [{"type": "tableau|schéma|illustration", "description": "..."}],
    "game_elements": ["cartes", "jetons", ...],
    "rules": [{"rule": "règle spécifique", "context": "contexte"}],
    "sections": [{"title": "...", "type": "setup|gameplay|scoring|endgame", "content": "..."}]
}"""

                message = HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data['data']}"}
                    }
                ])
                
                # Estimation tokens vision (prompt + image)
                prompt_tokens = len(prompt) // 4  # Approximation 4 chars = 1 token
                image_tokens = self._estimate_image_tokens(image_data['data'])
                estimated_input_tokens = prompt_tokens + image_tokens
                
                response = self.vision_model.invoke([message])
                
                # Estimation tokens output
                output_tokens = len(response.content) // 4
                total_vision_tokens = estimated_input_tokens + output_tokens
                
                print(f"✅ RAG: Page analysée (vision AI) - {len(response.content)} caractères")
                print(f"💰 Vision tokens: input≈{estimated_input_tokens}, output≈{output_tokens}, total≈{total_vision_tokens}")
                
                return response.content, total_vision_tokens
                
            except Exception as e:
                print(f"❌ RAG: Erreur analyse vision: {e}")
                # Fallback simulation
                pass
        
        # Simulation si vision non disponible
        simulated_analysis = {
            "text_content": f"[Texte simulé de {image_data.get('name', 'image')}]",
            "diagrams": [{"type": "tableau", "description": "Tableau de scores simulé"}],
            "game_elements": ["cartes", "jetons", "plateau"],
            "sections": [{"title": "Setup", "type": "setup", "content": "Instructions de mise en place"}]
        }
        
        print(f"⚠️ RAG: Page analysée (simulation) - {len(str(simulated_analysis))} caractères")
        return simulated_analysis, 0  # 0 tokens pour simulation
    
    def _estimate_image_tokens(self, base64_data):
        """Estimation approximative des tokens d'image basée sur la taille"""
        # GPT-4V utilise ~85 tokens pour une image 512x512
        # Estimation basée sur la taille base64 (très approximative)
        image_size_bytes = len(base64_data) * 3 // 4  # Conversion base64 vers bytes
        
        if image_size_bytes < 50000:  # < 50KB
            return 85
        elif image_size_bytes < 200000:  # < 200KB
            return 170
        else:  # > 200KB
            return 255
    
    def retrieve_relevant_rules(self, user_query, game_context=None):
        """Recherche les règles pertinentes pour une question"""
        print(f"🔎 RAG: Recherche pour '{user_query[:50]}...'")
        
        # Recherche vectorielle si composants disponibles
        if self.embeddings and self.vector_store:
            try:
                # Recherche par similarité
                similar_chunks = self.vector_store.similarity_search(
                    user_query, 
                    k=5,  # Top 5 résultats
                    filter={"game": game_context} if game_context else None
                )
                
                if similar_chunks:
                    context = self._format_context(similar_chunks)
                    print(f"✅ RAG: {len(similar_chunks)} chunks trouvés")
                    return context
                else:
                    print("⚠️ RAG: Aucun contexte trouvé")
                    return None
                    
            except Exception as e:
                print(f"❌ RAG: Erreur recherche vectorielle: {e}")
                return None
        else:
            print("⚠️ RAG: Composants non configurés, retour simulation")
            return f"[Context RAG simulé pour: {user_query[:30]}...]"
    
    def _store_in_vector_db(self, extracted_data):
        """Stocke l'analyse dans la base vectorielle avec chunking intelligent"""
        print(f"💾 RAG: Stockage de {len(extracted_data)} pages analysées")
        
        if self.vector_store:
            try:
                documents = []
                metadatas = []
                
                for page_idx, data in enumerate(extracted_data):
                    chunks = self._create_smart_chunks(data, page_idx + 1)
                    documents.extend([chunk['text'] for chunk in chunks])
                    metadatas.extend([chunk['metadata'] for chunk in chunks])
                
                # Estimation tokens embeddings (approximation)
                total_chars = sum(len(doc) for doc in documents)
                estimated_embedding_tokens = total_chars // 4  # 4 chars ≈ 1 token
                
                # Ajouter au vector store
                self.vector_store.add_texts(
                    texts=documents,
                    metadatas=metadatas
                )
                
                print(f"✅ RAG: {len(documents)} chunks stockés dans ChromaDB ({len(extracted_data)} pages → {len(documents)} chunks)")
                print(f"💰 Embeddings tokens: ≈{estimated_embedding_tokens} tokens pour {total_chars} caractères")
                
                return estimated_embedding_tokens
                
            except Exception as e:
                print(f"❌ RAG: Erreur stockage ChromaDB: {e}")
                self._store_simulation(extracted_data)
                return 0
        else:
            print("⚠️ RAG: ChromaDB non configuré, stockage simulation")
            self._store_simulation(extracted_data)
            return 0
    
    def _create_smart_chunks(self, page_data, page_num):
        """Découpe une page en chunks intelligents"""
        chunks = []
        
        if isinstance(page_data, str):
            # Si c'est du JSON string, essayer de parser
            try:
                import json
                data = json.loads(page_data)
            except:
                # Sinon chunker par taille
                return self._chunk_by_size(page_data, page_num)
        elif isinstance(page_data, dict):
            data = page_data
        else:
            return self._chunk_by_size(str(page_data), page_num)
        
        # Chunking par sections si structure JSON disponible
        if 'sections' in data and data['sections']:
            for i, section in enumerate(data['sections']):
                chunk_text = f"Section: {section.get('title', 'Sans titre')}\n"
                chunk_text += f"Type: {section.get('type', 'général')}\n"
                chunk_text += f"Contenu: {section.get('content', '')}"
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'page': page_num,
                        'chunk_type': 'section',
                        'section_type': section.get('type', 'général'),
                        'section_title': section.get('title', f'Section {i+1}'),
                        'source': 'game_rules'
                    }
                })
        
        # Chunking par règles si disponible
        if 'rules' in data and data['rules']:
            for i, rule in enumerate(data['rules']):
                chunk_text = f"Règle: {rule.get('rule', '')}\n"
                chunk_text += f"Contexte: {rule.get('context', '')}"
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'page': page_num,
                        'chunk_type': 'rule',
                        'rule_id': i + 1,
                        'source': 'game_rules'
                    }
                })
        
        # Fallback: tout le contenu texte si pas de structure
        if not chunks and 'text_content' in data:
            chunks.extend(self._chunk_by_size(data['text_content'], page_num))
        
        return chunks if chunks else [{'text': str(page_data)[:1000], 'metadata': {'page': page_num, 'chunk_type': 'fallback', 'source': 'game_rules'}}]
    
    def _chunk_by_size(self, text, page_num, max_size=500):
        """Découpe par taille avec préservation des phrases"""
        chunks = []
        sentences = text.split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + sentence) < max_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'metadata': {
                            'page': page_num,
                            'chunk_type': 'text_segment',
                            'source': 'game_rules'
                        }
                    })
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': {
                    'page': page_num,
                    'chunk_type': 'text_segment',
                    'source': 'game_rules'
                }
            })
        
        return chunks
    
    def _store_simulation(self, extracted_data):
        """Stockage simulation en mémoire"""
        for data in extracted_data:
            self.analyzed_documents.append({
                "content": str(data)[:200] + "...",
                "timestamp": "now"
            })
        print(f"📚 RAG: {len(self.analyzed_documents)} documents total en mémoire (simulation)")
    
    def _format_context(self, chunks):
        """Formate le contexte récupéré pour le prompt"""
        if not chunks:
            return None
            
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk.page_content[:500]  # Limiter la taille
            context_parts.append(f"[Règle {i}] {content}")
        
        return "\n\n".join(context_parts)
    
    def clear_vector_store(self):
        """Vide complètement le store vectoriel"""
        if self.vector_store:
            try:
                # Récupérer tous les documents pour les supprimer
                collection = self.vector_store._collection
                
                # Récupérer tous les IDs des documents
                all_docs = collection.get()
                
                if all_docs['ids']:
                    # Supprimer tous les documents par leurs IDs
                    collection.delete(ids=all_docs['ids'])
                    print(f"🗑️ RAG: {len(all_docs['ids'])} documents supprimés du store vectoriel")
                else:
                    print("🗑️ RAG: Store vectoriel déjà vide")
                
                # Vider aussi le cache simulation
                self.analyzed_documents = []
                
            except Exception as e:
                print(f"❌ RAG: Erreur vidage store: {e}")
                raise e
        else:
            print("⚠️ RAG: Pas de store vectoriel à vider")
    
    def get_vector_store_info(self):
        """Retourne des infos sur le store vectoriel"""
        if self.vector_store:
            try:
                collection = self.vector_store._collection
                count = collection.count()
                return {
                    "document_count": count,
                    "store_type": "ChromaDB",
                    "has_documents": count > 0
                }
            except:
                return {
                    "document_count": 0,
                    "store_type": "ChromaDB",
                    "has_documents": False
                }
        else:
            return {
                "document_count": len(self.analyzed_documents),
                "store_type": "Simulation",
                "has_documents": len(self.analyzed_documents) > 0
            }
