from classes.settings import Settings


class AgentManager:

    _instance = None
    _chat_model = None
    _settings: Settings = None
    _conversation_history = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, settings, tools):
        self._settings = settings
        if self._chat_model is None:
            self._chat_model = settings.agent_model
        return self

    def invoke(self, message_data, rag_context=None):
        """Appel direct au modèle Azure OpenAI avec support RAG hybride"""

        # Analyser le contexte RAG pour déterminer s'il y a des images
        rag_images = []
        if rag_context and isinstance(rag_context, dict) and rag_context.get("type") == "hybrid":
            rag_images = rag_context.get("images", [])
            print(f"🖼️ Agent: Contexte RAG hybride avec {len(rag_images)} images")
            
            # Logs détaillés des images reçues
            for i, img in enumerate(rag_images, 1):
                original_name = img['metadata'].get('original_name', 'inconnu')
                image_id = img.get('image_id', 'inconnu')
                image_size = len(img['image_data']) // 1024 if 'image_data' in img else 0
                print(f"   📄 Image RAG {i}: {original_name} (ID: {image_id}, ~{image_size}KB)")
        elif rag_context and isinstance(rag_context, dict) and rag_context.get("type") == "text":
            context_preview = rag_context.get("context", "")[:100] + "..." if len(rag_context.get("context", "")) > 100 else rag_context.get("context", "")
            print(f"📝 Agent: Contexte RAG classique")
            print(f"   💬 Contexte: {context_preview}")
        elif rag_context and isinstance(rag_context, str):
            context_preview = rag_context[:100] + "..." if len(rag_context) > 100 else rag_context
            print(f"📝 Agent: Contexte RAG textuel (ancien format)")
            print(f"   💬 Contexte: {context_preview}")

        # Préparer les messages (contexte RAG intégré dans le system prompt)
        messages = [{"role": "system", "content": self._build_system_prompt(rag_context)}]

        # Ajouter l'historique de conversation
        messages.extend(self._conversation_history)
        
        # Traiter le message utilisateur
        user_content = self._build_user_content(message_data["input"], rag_images)
        user_message = {"role": "user", "content": user_content}
        
        messages.append(user_message)
        
        # Debug: compter les tokens approximativement
        total_chars = sum(len(str(msg)) for msg in messages)
        print(f"DEBUG: Envoi de ~{total_chars} caractères ({total_chars//4} tokens approx)")
        print(f"DEBUG: {len(messages)} messages, {len(rag_images)} images RAG")
        
        # Appeler le modèle
        response = self._chat_model.invoke(messages)
        
        # Sauvegarder dans l'historique (sans les images pour économiser les tokens)
        history_user_message = self._create_history_user_message(message_data["input"], rag_images)
        
        self._conversation_history.append(history_user_message)
        self._conversation_history.append({"role": "assistant", "content": response.content})
        
        # Limiter l'historique (garder seulement les 10 derniers échanges)
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-20:]
        
        return {"output": response.content}
    
    def _build_user_content(self, input_content, rag_images):
        """Construit le contenu utilisateur avec images RAG et question"""
        if not rag_images and isinstance(input_content, str):
            # Cas simple : texte seul
            return input_content
        
        # Construire contenu multimodal
        content_parts = []
        
        # 1. Ajouter le texte de la question
        if isinstance(input_content, str):
            content_parts.append({"type": "text", "text": input_content})
        else:
            # input_content est déjà une liste (images de question directe)
            content_parts.extend(input_content)
        
        # 2. Ajouter les images du RAG hybride
        if rag_images:
            content_parts.append({
                "type": "text", 
                "text": f"\n\n🔍 CONTEXTE VISUEL RAG ({len(rag_images)} images pertinentes):"
            })
            
            for i, rag_image in enumerate(rag_images, 1):
                content_parts.append({
                    "type": "text",
                    "text": f"\n[Image RAG {i}] {rag_image['metadata'].get('original_name', 'document')}:"
                })
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{rag_image['image_data']}"}
                })
        
        return content_parts
    
    def _create_history_user_message(self, input_content, rag_images):
        """Crée le message historique sans images pour économiser tokens"""
        if isinstance(input_content, str):
            text_content = input_content
        else:
            # Extraire seulement le texte des content parts
            text_parts = [item["text"] for item in input_content if item.get("type") == "text"]
            text_content = " ".join(text_parts)
        
        # Ajouter info sur les images sans les inclure
        if rag_images:
            text_content += f" [+ {len(rag_images)} images RAG analysées]"
        
        return {"role": "user", "content": text_content}

    def clear_memory(self):
        """Vider l'historique de conversation"""
        self._conversation_history = []

    def _build_system_prompt(self, rag_context=None):
        """Construit le prompt système avec contexte RAG optionnel"""
        base_prompt = self._settings.system_prompt
        
        if rag_context:
            # Gérer les deux types de contexte RAG
            if isinstance(rag_context, dict):
                if rag_context.get("type") == "hybrid":
                    # RAG Hybride : contexte textuel + info sur images
                    context_text = rag_context.get("context", "")
                    image_count = rag_context.get("image_count", 0)
                    
                    enhanced_prompt = f"""{base_prompt}

CONTEXTE RAG HYBRIDE:
{context_text}

IMPORTANT: Tu recevras {image_count} images de contexte avec cette question. 
Ces images contiennent des règles, schémas ou diagrammes pertinents à la question.
Analyse ces images en détail et utilise-les comme référence principale pour ta réponse.
Combine l'information textuelle ci-dessus avec l'analyse visuelle des images."""
                
                elif rag_context.get("type") == "text":
                    # RAG Classique : contexte textuel seulement
                    enhanced_prompt = f"""{base_prompt}

CONTEXTE ADDITIONNEL DES RÈGLES:
{rag_context.get("context", "")}

Utilise ce contexte pour enrichir tes réponses, mais reste précis et factuel."""
                
                else:
                    # Format dict inconnu, utiliser comme texte
                    enhanced_prompt = f"""{base_prompt}

CONTEXTE ADDITIONNEL DES RÈGLES:
{str(rag_context)}

Utilise ce contexte pour enrichir tes réponses, mais reste précis et factuel."""
            
            else:
                # Ancien format string (compatibilité)
                enhanced_prompt = f"""{base_prompt}

CONTEXTE ADDITIONNEL DES RÈGLES:
{rag_context}

Utilise ce contexte pour enrichir tes réponses, mais reste précis et factuel."""
            
            return enhanced_prompt
        
        return base_prompt

    @property
    def executor(self):
        # Pour compatibilité avec l'interface existante
        return self