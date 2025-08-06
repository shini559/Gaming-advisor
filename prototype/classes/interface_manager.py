from abc import ABC
from datetime import datetime

import streamlit as st
from streamlit_extras.let_it_rain import rain

from classes.settings import Settings
from classes.message_manager import MessageManager
from classes.rag_manager import RAGManager


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

        # Initialize RAG Manager
        if not hasattr(cls, 'rag_manager'):
            cls.rag_manager = RAGManager(settings)

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
        cls._important_context()
        cls._file_uploader()
        cls._debug_checkbox()
        cls._reset_button()
        cls._clear_rag_button()
        cls._unsatisfied_button()
        cls._satisfied_button()

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
            
            # Bouton de vectorisation
            if hasattr(cls, 'rag_manager') and cls.rag_manager.embeddings:
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
    def _important_context(cls) -> None:
        """ Stores the debug information in the messages. """
        st.sidebar.markdown("""
            <div class="footer-info">
                <strong>ℹ️ Attention :</strong><br>
                Ce chatbot est conçu pour vous assister dans vos parties grâce à l'IA. 
                Ses informations peuvent être erronées.
            </div>
            """, unsafe_allow_html=True)

    @classmethod
    def _debug_checkbox(cls) -> None:
        """ Prints and handles a debug checkbox. """
        debug_mode = st.sidebar.checkbox("Afficher debug", value=st.session_state.debug_mode)

        # Mise à jour de settings.params['debug']
        if debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_mode
            st.rerun()

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
        """ A button to clear the RAG vector store. """
        if hasattr(cls, 'rag_manager') and cls.rag_manager.vector_store:
            if st.sidebar.button("🗑️ Vider le store RAG", help="Supprime tous les documents vectorisés"):
                try:
                    # Vider le store vectoriel
                    cls.rag_manager.clear_vector_store()
                    st.sidebar.success("✅ Store RAG vidé !")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"❌ Erreur: {e}")

    @classmethod
    def _unsatisfied_button(cls):
        """ A button that triggers a happy reaction """
        if st.sidebar.button("Je ne suis pas satisfait"):
            rain(
                emoji="😞",
                font_size=54,
                falling_speed=3,
                animation_length=1,
            )

    @classmethod
    def _satisfied_button(cls):
        """ A button that triggers a happy reaction """
        if st.sidebar.button("Je suis satisfait"):
            st.balloons()

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