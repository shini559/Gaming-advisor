from abc import ABC
from datetime import datetime

import streamlit as st
from streamlit_extras.let_it_rain import rain

from classes.settings import Settings
from classes.message_manager import MessageManager
from classes.rag_factory import RAGFactory, RAGType, get_rag_type_from_string
from classes.log_capture import log_capture


class InterfaceManager(ABC):
    """
    A class for managing the Streamlit interface.

    This class handles the user interface elements using Streamlit,
    including initialization with settings and an agent manager.

    Methods:
    --------
    initialize(settings:Settings, agent_manager):
        Initializes the interface.
    """
    _settings:Settings = None

    @classmethod
    def initialize(cls, settings:Settings, agent_manager) -> None:
        """
        Initializes the interface.

        Parameters:
        -----------
        settings: Settings
            A Settings object
        agent_manager: AgentManager
            Provides the agent
        """
        cls._settings = settings
        cls._create_interface(agent_manager, settings)

    @classmethod
    def _create_interface(cls, agent_manager, settings:Settings):
        """
        Creates the interface for the chat.

        Parameters:
        -----------
        agent_manager: AgentManager
            an AgentManager object
        """
        cls._header()

        if "debug_mode" not in st.session_state:
            st.session_state.debug_mode = cls._settings.params["debug"]

        cls._sidebar()

        if "agent_executor" not in st.session_state:
            st.session_state.agent_executor = agent_manager

        # Initialize RAG Manager via Factory
        if not hasattr(cls, 'rag_manager') or not cls.rag_manager:
            # Default to classic RAG
            rag_type = getattr(st.session_state, 'rag_type', RAGType.CLASSIC)
            cls.rag_manager = RAGFactory.create_rag(rag_type, settings)

        # Message history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        cls._body(settings)
        cls._css()

    @classmethod
    def _header(cls) -> None:
        """ Shows the header of the chat. """
        st.set_page_config(
            page_title="GameAdvisor",
            page_icon="🇫🇷",
            layout="centered",
            initial_sidebar_state="expanded"
        )

        st.markdown("""
            <div class="main-header">
                <h1>GameAdvisor : la fin des parties interminables</h1>
                <p>Il se tape les règles, vous vous tapez des barres</p>
            </div>
            """, unsafe_allow_html=True)

    @classmethod
    def _body(cls, settings:Settings) -> None:
        """ The body of the chat. """
        cls._messages()
        cls._question_image_uploader()
        cls._debug_logs_display()
        cls._user_input(settings)

    @classmethod
    def _user_input(cls, settings:Settings) -> None:
        """ Shows and handles the user input. """
        if prompt := st.chat_input("Posez votre question…"):
            cls._css()

            # Handle uploaded files - Plus de vectorisation automatique
            uploaded_files = getattr(st.session_state, 'uploaded_files', None)
            files_info = []  # Par défaut, pas d'images envoyées à l'agent
            
            # Si l'utilisateur n'a pas vectorisé, proposer mode classique
            if uploaded_files:
                if not (hasattr(cls, 'rag_manager') and cls.rag_manager.embeddings):
                    # Mode classique : envoyer les images à l'agent
                    files_info = MessageManager.process_uploaded_files(uploaded_files, settings, None)
                    st.sidebar.warning("⚠️ RAG non configuré, envoi des images brutes")
                else:
                    # L'utilisateur doit utiliser le bouton pour vectoriser
                    st.sidebar.warning("💡 Utilisez le bouton 'Vectoriser les documents' d'abord")

            # NOUVEAU: Handle question-specific images (uploaded via chat area)
            question_images = getattr(st.session_state, 'question_images', None)
            if question_images:
                # Traiter les images de question directement (pas de vectorisation)
                question_files_info = MessageManager.process_uploaded_files(question_images, settings, None)
                files_info.extend(question_files_info)
                # Nettoyer après usage
                del st.session_state.question_images

            # NOUVEAU: Recherche RAG (maintenant que les docs sont vectorisés)
            rag_context = None
            if hasattr(cls, 'rag_manager'):
                rag_context = cls.rag_manager.retrieve_relevant_rules(prompt)


            # Prepare user & agent messages
            user_message = prompt + '  \n  \n' + MessageManager.get_files_summary(files_info)
            agent_message = MessageManager.create_agent_message(prompt, files_info)

            # Print user message
            st.session_state.messages.append({"role": "user", "content": user_message, "type": "user"})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant message
            with st.chat_message("assistant"):
                with st.spinner("Réflexion en cours..."):

                    response = st.session_state.agent_executor.invoke(agent_message, rag_context)

                    # Append response to history
                    st.session_state.chat_history.append({
                        "user": prompt,
                        "assistant": response["output"],
                        "timestamp": datetime.now()
                    })

                    # Format & print response
                    st.markdown(response["output"])
                    st.session_state.messages.append({"role": "assistant", "content": response["output"], "type": "ai"})

            if hasattr(st.session_state, 'uploaded_files'):
                del st.session_state.uploaded_files

            st.rerun()

    @classmethod
    def _sidebar(cls) -> None:
        """ The sidebar of the chat. """
        cls._rag_method_selector()
        cls._file_uploader()
        cls._debug_checkbox()
        cls._reset_button()
        cls._clear_rag_button()

    @classmethod
    def _file_uploader(cls):
        """ File uploader for images and PDFs """
        st.sidebar.markdown("### 📎 Joindre des fichiers")
        uploaded_files = st.sidebar.file_uploader(
            "Choisir des fichiers (images, PDFs)",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files
            st.sidebar.success(f"{len(uploaded_files)} fichier(s) ajouté(s)")
            
            # Logique de traitement selon le type de RAG
            current_rag_type = getattr(st.session_state, 'rag_type', RAGType.CLASSIC)
            
            if current_rag_type == RAGType.DIRECT:
                # Mode direct : juste stocker les images
                if st.sidebar.button("📋 Stocker pour envoi direct", type="primary"):
                    with st.spinner("Préparation des images..."):
                        from classes.message_manager import MessageManager
                        images_data = MessageManager.process_uploaded_files(uploaded_files, cls._settings, None)
                        
                        # Stocker dans le DirectRAGAdapter
                        cls.rag_manager.process_game_document(images_data)
                        
                        st.sidebar.success("✅ Images prêtes pour envoi direct !")
                        
                        # Supprimer les fichiers uploadés
                        del st.session_state.uploaded_files
                        st.rerun()
                        
                st.sidebar.info("👆 Les images seront envoyées directement au modèle")
                
            elif hasattr(cls, 'rag_manager') and cls.rag_manager.embeddings:
                # Mode classique/hybride : vectorisation
                if st.sidebar.button("🚀 Vectoriser les documents", type="primary"):
                    with st.spinner("Vectorisation en cours..."):
                        from classes.message_manager import MessageManager
                        tokens_info = MessageManager.process_and_vectorize_files(
                            uploaded_files, cls._settings, cls.rag_manager
                        )
                        
                        if tokens_info:
                            st.sidebar.success("✅ Documents vectorisés !")
                            st.sidebar.info(f"💰 Coût: ~{tokens_info.get('total_tokens', 0)} tokens")
                        else:
                            st.sidebar.success("✅ Documents vectorisés !")
                        
                        # Supprimer les fichiers uploadés pour éviter re-vectorisation
                        del st.session_state.uploaded_files
                        st.rerun()
                        
                st.sidebar.info("👆 Cliquez pour lancer l'analyse IA des règles")
            else:
                st.sidebar.warning("⚠️ RAG non configuré")

        return uploaded_files

    @classmethod  
    def _rag_method_selector(cls) -> None:
        """ RAG method selector """
        st.sidebar.markdown("### 🎯 Méthode RAG")
        
        # Options disponibles
        rag_options = {
            "Classique": RAGType.CLASSIC,
            "Hybride": RAGType.HYBRID,
            "Direct": RAGType.DIRECT
        }
        
        # Récupérer choix actuel
        current_type = getattr(st.session_state, 'rag_type', RAGType.CLASSIC)
        current_index = 0
        if current_type == RAGType.HYBRID:
            current_index = 1
        elif current_type == RAGType.DIRECT:
            current_index = 2
        
        # Sélecteur radio
        selected_option = st.sidebar.radio(
            "Choisir la méthode RAG:",
            options=list(rag_options.keys()),
            index=current_index,
            help="Classique: Texte vectorisé\nHybride: Métadonnées + Images directes\nDirect: Images envoyées directement sans RAG"
        )
        
        selected_type = rag_options[selected_option]
        
        # Si changement de type
        if selected_type != getattr(st.session_state, 'rag_type', RAGType.CLASSIC):
            st.session_state.rag_type = selected_type
            
            # Changer de RAG via factory (forcer recréation pour éviter le cache)
            try:
                cls.rag_manager = RAGFactory.create_rag(selected_type, cls._settings, force_recreate=True)
                st.sidebar.success(f"✅ Basculé vers RAG {selected_option}")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ Erreur changement RAG: {e}")
        
        # Afficher infos sur le RAG actuel
        if hasattr(cls, 'rag_manager'):
            try:
                info = cls.rag_manager.get_vector_store_info()
                rag_type_display = info.get("rag_type", "Inconnu")
                doc_count = info.get("document_count", 0)
                
                if selected_type == RAGType.HYBRID:
                    image_count = info.get("image_count", 0)
                    st.sidebar.info(f"📊 **{rag_type_display}**\n\n{doc_count} métadonnées, {image_count} images")
                elif selected_type == RAGType.DIRECT:
                    image_count = info.get("image_count", 0)
                    st.sidebar.info(f"📊 **{rag_type_display}**\n\n{image_count} images prêtes")
                else:
                    st.sidebar.info(f"📊 **{rag_type_display}**\n\n{doc_count} documents")
                    
            except Exception as e:
                st.sidebar.warning(f"⚠️ Infos RAG indisponibles: {e}")

    @classmethod
    def _question_image_uploader(cls) -> None:
        """ Image uploader for one-time questions in the main chat area """
        with st.expander("📷 Joindre une image à votre question", expanded=False):
            st.markdown("**Pour cette question uniquement** (pas de vectorisation)")
            question_images = st.file_uploader(
                "Ajouter une image pour illustrer votre question",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=True,
                key="question_image_uploader",
                help="Ces images seront envoyées directement avec votre question, sans être vectorisées dans le RAG"
            )
            
            if question_images:
                st.session_state.question_images = question_images
                st.success(f"🖼️ {len(question_images)} image(s) prête(s) pour la prochaine question")
                
                # Aperçu des images
                cols = st.columns(min(len(question_images), 3))
                for i, img in enumerate(question_images[:3]):  # Max 3 previews
                    with cols[i % 3]:
                        st.image(img, caption=img.name, width=100)
                
                if len(question_images) > 3:
                    st.info(f"... et {len(question_images) - 3} autre(s)")

    @classmethod
    def _debug_logs_display(cls) -> None:
        """ Affiche les logs de debug si le mode debug est activé """
        if not st.session_state.debug_mode:
            return
            
        # Récupérer les logs récents
        logs = log_capture.get_recent_logs(limit=200)
        
        if logs:
            with st.expander("📊 Console Debug (logs temps réel)", expanded=False):
                # Bouton pour vider les logs
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🗑️ Vider logs"):
                        log_capture.clear_logs()
                        st.rerun()
                
                with col2:
                    st.write(f"**{len(logs)} entrées de log**")
                
                # Container pour les logs avec scrolling
                log_container = st.container()
                
                with log_container:
                    # Afficher les logs dans l'ordre chronologique inverse (plus récents en haut)
                    for log_entry in reversed(logs[-50:]):  # Limiter à 50 logs pour éviter la surcharge
                        timestamp = log_entry['timestamp'].strftime("%H:%M:%S.%f")[:-3]
                        message = log_entry['message']
                        is_error = log_entry['is_error']
                        
                        # Style différent pour les erreurs
                        if is_error:
                            st.markdown(f"""
                                <div style="
                                    background-color: #f8d7da; 
                                    color: #721c24; 
                                    padding: 5px 10px; 
                                    border-radius: 4px; 
                                    border-left: 4px solid #dc3545;
                                    margin: 2px 0;
                                    font-family: 'Courier New', monospace;
                                    font-size: 12px;
                                ">
                                    <strong>[{timestamp}] ❌</strong> {message}
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Coloration selon le type de log
                            if any(keyword in message for keyword in ['✅', 'SUCCESS', 'success']):
                                bg_color = "#d4edda"
                                text_color = "#155724" 
                                border_color = "#28a745"
                            elif any(keyword in message for keyword in ['⚠️', 'WARNING', 'warning']):
                                bg_color = "#fff3cd"
                                text_color = "#856404"
                                border_color = "#ffc107"
                            elif any(keyword in message for keyword in ['🔍', 'DEBUG', 'debug']):
                                bg_color = "#e2e3e5"
                                text_color = "#383d41"
                                border_color = "#6c757d"
                            elif any(keyword in message for keyword in ['🔄', 'PROCESSING', 'processing']):
                                bg_color = "#cce7ff"
                                text_color = "#004085"
                                border_color = "#007bff"
                            else:
                                bg_color = "#f8f9fa"
                                text_color = "#495057"
                                border_color = "#dee2e6"
                            
                            st.markdown(f"""
                                <div style="
                                    background-color: {bg_color}; 
                                    color: {text_color}; 
                                    padding: 5px 10px; 
                                    border-radius: 4px; 
                                    border-left: 4px solid {border_color};
                                    margin: 2px 0;
                                    font-family: 'Courier New', monospace;
                                    font-size: 12px;
                                    line-height: 1.4;
                                ">
                                    <strong>[{timestamp}]</strong> {message}
                                </div>
                            """, unsafe_allow_html=True)

    @classmethod
    def _messages(cls) -> None:
        """ Prints the messages in the chat. """
        for message in st.session_state.messages:
            if message["type"] == "debug":
                if st.session_state.debug_mode:
                    st.markdown(f'<div class="debug-message">{message["content"]}</div>', unsafe_allow_html=True)
            elif message["type"] == "debug-source":
                if st.session_state.debug_mode:
                    with st.expander(message["content"]):
                        st.markdown(f"```\n{message['extended-content']}\n```")
            else:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    @classmethod
    def _debug_checkbox(cls) -> None:
        """ Prints and handles a debug checkbox. """
        debug_mode = st.sidebar.checkbox("Afficher debug", value=st.session_state.debug_mode)

        # Gestion de la capture des logs
        if debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_mode
            
            if debug_mode:
                # Démarrer la capture des logs
                log_capture.start_capture()
                log_capture.clear_logs()  # Vider les anciens logs
            else:
                # Arrêter la capture des logs
                log_capture.stop_capture()
                
            st.rerun()
        
        # Gérer la capture pendant que le mode debug est actif
        if debug_mode and not log_capture.is_capturing:
            log_capture.start_capture()
        elif not debug_mode and log_capture.is_capturing:
            log_capture.stop_capture()

    @classmethod
    def _reset_button(cls) -> None:
        """ A reset button for the chat. """
        if st.sidebar.button("Réinitialiser la conversation"):
            st.session_state.messages = []
            if "agent_executor" in st.session_state:
                st.session_state.agent_executor.clear_memory()
            st.rerun()

    @classmethod
    def _clear_rag_button(cls) -> None:
        """ Buttons to clear different RAG vector stores. """
        st.sidebar.markdown("### 🗑️ Vider les stores")
        
        # Récupérer les infos de tous les stores via la Factory
        try:
            all_stores_info = RAGFactory.get_all_store_info()
            
            # Bouton pour vider le store RAG Classique
            classic_info = all_stores_info.get('classic', {})
            classic_doc_count = classic_info.get('document_count', 0)
            
            if st.sidebar.button(
                f"🗑️ Vider RAG Classique ({classic_doc_count})", 
                help="Supprime tous les documents vectorisés du RAG classique",
                disabled=classic_doc_count == 0
            ):
                try:
                    # Créer temporairement une instance RAG classique pour la vider
                    classic_rag = RAGFactory.create_rag(RAGType.CLASSIC, cls._settings, force_recreate=False)
                    classic_rag.clear_vector_store()
                    st.sidebar.success("✅ Store RAG Classique vidé !")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"❌ Erreur RAG Classique: {e}")
            
            # Bouton pour vider le store RAG Hybride
            hybrid_info = all_stores_info.get('hybrid', {})
            hybrid_doc_count = hybrid_info.get('document_count', 0)
            hybrid_image_count = hybrid_info.get('image_count', 0)
            
            if st.sidebar.button(
                f"🗑️ Vider RAG Hybride ({hybrid_doc_count}/{hybrid_image_count})", 
                help="Supprime toutes les métadonnées et images du RAG hybride",
                disabled=hybrid_doc_count == 0 and hybrid_image_count == 0
            ):
                try:
                    # Créer temporairement une instance RAG hybride pour la vider
                    hybrid_rag = RAGFactory.create_rag(RAGType.HYBRID, cls._settings, force_recreate=False)
                    hybrid_rag.clear_vector_store()
                    st.sidebar.success("✅ Store RAG Hybride vidé !")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"❌ Erreur RAG Hybride: {e}")
            
                    
        except Exception as e:
            # Fallback si erreur récupération infos
            st.sidebar.error(f"❌ Erreur récupération infos stores: {e}")
            
            # Bouton de secours pour vider le store actuel
            current_rag_type = getattr(st.session_state, 'rag_type', RAGType.CLASSIC)
            if hasattr(cls, 'rag_manager') and st.sidebar.button("🗑️ Vider store actuel"):
                try:
                    cls.rag_manager.clear_vector_store()
                    st.sidebar.success("✅ Store actuel vidé !")
                    st.rerun()
                except Exception as clear_error:
                    st.sidebar.error(f"❌ Erreur: {clear_error}")

    @classmethod
    def _css(cls) -> None:
        """ CSS for the chat. """
        st.markdown("""
                <style>
                button[kind="header"], button[kind="headerNoPadding"], div[aria-label="dialog"], ul[role="option"] {
                    color: Snow;
                }
                .main-header {
                    background: linear-gradient(135deg, #ff7d00 0%, #ffecd1 100%);
                    padding: 40px 20px;
                    border-radius: 15px;
                    margin-bottom: 2rem;
                    text-align: center;
                    color: white;
                    box-shadow: 0 4px 4px rgba(0,0,0,0.1);
                }
                .main-header h1 {
                    font-size: 2.5rem;
                    margin-bottom: 0.5rem;
                    font-weight: 700;
                }
                .main-header p {
                    font-size: 1.1rem;
                    opacity: 0.9;
                    margin: 0;
                }
                .stChatMessage {
                    background-color: Snow;
                    border-left: 2px solid DarkOrange;
                    border-bottom: 2px solid DarkOrange;
                }
                .debug-message {
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ffeeba;
                    font-family: monospace;
                    margin-bottom: 10px;
                }
                .stExpander {
                    font-weight: bold;
                    color: #856404;
                    background-color: #fff3cd;
                    padding: 8px;
                    border-radius: 5px;
                }
                .stExpanderDetail {
                    background-color: #fffbea;
                    padding: 10px;
                    border: 1px solid #ffeeba;
                    border-radius: 5px;
                }
                </style>
            """, unsafe_allow_html=True)