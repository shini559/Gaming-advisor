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

    def invoke(self, message_data):
        """Appel direct au modèle Azure OpenAI sans agent ReAct"""
        
        # Préparer les messages
        messages = [{"role": "system", "content": self._settings.system_prompt}]
        
        # Ajouter l'historique de conversation
        messages.extend(self._conversation_history)
        
        # Traiter le message utilisateur
        user_message = {"role": "user", "content": message_data["input"]}
        
        messages.append(user_message)
        
        # Debug: compter les tokens approximativement
        total_chars = sum(len(str(msg)) for msg in messages)
        print(f"DEBUG: Envoi de ~{total_chars} caractères ({total_chars//4} tokens approx)")
        print(f"DEBUG: {len(messages)} messages dans l'historique")
        
        # Appeler le modèle
        response = self._chat_model.invoke(messages)
        
        # Sauvegarder dans l'historique (sans les images pour économiser les tokens)
        if isinstance(message_data["input"], str):
            # Message texte simple
            history_user_message = user_message
        else:
            # Pour les images, ne garder que le texte dans l'historique
            text_content = ""
            for content_item in message_data["input"]:
                if content_item["type"] == "text":
                    text_content += content_item["text"]
            history_user_message = {"role": "user", "content": text_content + " [Images analysées précédemment]"}
        
        self._conversation_history.append(history_user_message)
        self._conversation_history.append({"role": "assistant", "content": response.content})
        
        # Limiter l'historique (garder seulement les 10 derniers échanges)
        if len(self._conversation_history) > 20:
            self._conversation_history = self._conversation_history[-20:]
        
        return {"output": response.content}

    def clear_memory(self):
        """Vider l'historique de conversation"""
        self._conversation_history = []

    @property
    def executor(self):
        # Pour compatibilité avec l'interface existante
        return self