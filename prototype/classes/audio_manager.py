import azure.cognitiveservices.speech as speechsdk
import tempfile
import os
import base64
from typing import Optional, Union
import logging
import io

from classes.settings import Settings

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger(__name__)

class BinaryFileReaderCallback(speechsdk.audio.PullAudioInputStreamCallback):
    """
    Callback pour lire les fichiers audio compressés (WebM, OGG, MP3, etc.)
    Basé sur la documentation Microsoft Azure Speech Service
    """
    def __init__(self, filename: str):
        super().__init__()
        self._file_h = open(filename, "rb")

    def read(self, buffer: memoryview) -> int:
        """Lit les données audio depuis le fichier"""
        try:
            size = buffer.nbytes
            frames = self._file_h.read(size)
            
            if not frames:
                return 0
                
            buffer[:len(frames)] = frames
            return len(frames)
        except Exception as e:
            logger.error(f"❌ Erreur lecture fichier audio: {e}")
            return 0

    def close(self) -> None:
        """Ferme le fichier"""
        try:
            self._file_h.close()
        except Exception as e:
            logger.error(f"❌ Erreur fermeture fichier: {e}")

class AudioManager:
    """
    Gestionnaire pour les fonctionnalités Azure Speech Service
    - Speech-to-Text (reconnaissance vocale)
    - Text-to-Speech (synthèse vocale)
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._speech_config = None
        self._init_speech_service()
    
    def _init_speech_service(self):
        """Initialise la configuration Azure Speech Service"""
        try:
            if not self.settings.azure_speech_key:
                logger.error("❌ AZURE_SPEECH_KEY manquante dans .env")
                raise ValueError("Clé Azure Speech Service manquante")
            
            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.settings.azure_speech_key,
                region=self.settings.azure_speech_region
            )
            
            # Configuration française
            self._speech_config.speech_recognition_language = "fr-FR"
            self._speech_config.speech_synthesis_language = "fr-FR"
            self._speech_config.speech_synthesis_voice_name = "fr-FR-DeniseNeural"
            
            logger.info(f"✅ Azure Speech Service initialisé (région: {self.settings.azure_speech_region})")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation Azure Speech: {e}")
            raise
    
    def _detect_audio_format(self, audio_bytes: bytes) -> str:
        """
        Détecte le format audio à partir des headers des bytes
        
        Args:
            audio_bytes: Audio en format bytes
            
        Returns:
            Format détecté ('wav', 'mp3', 'm4a', 'ogg', 'webm') ou 'unknown'
        """
        if len(audio_bytes) < 12:
            return 'unknown'
            
        # Vérifier les signatures de fichiers
        if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:12]:
            return 'wav'
        elif audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff\xfb'):
            return 'mp3'
        elif b'ftyp' in audio_bytes[:12] and (b'M4A' in audio_bytes[:20] or b'mp41' in audio_bytes[:20]):
            return 'm4a'
        elif audio_bytes.startswith(b'OggS'):
            return 'ogg'
        elif audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
            return 'webm'
        else:
            return 'unknown'
            
    def _create_temp_file_with_extension(self, audio_bytes: bytes) -> tuple[str, str]:
        """
        Crée un fichier temporaire avec l'extension appropriée selon le format
        
        Args:
            audio_bytes: Audio en format bytes
            
        Returns:
            Tuple (chemin_fichier, format_détecté)
        """
        detected_format = self._detect_audio_format(audio_bytes)
        
        # Mapper les extensions
        extension_map = {
            'wav': '.wav',
            'mp3': '.mp3', 
            'm4a': '.m4a',
            'ogg': '.ogg',
            'webm': '.webm',
            'unknown': '.wav'  # Par défaut
        }
        
        extension = extension_map.get(detected_format, '.wav')
        
        # Créer le fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
            
        logger.info(f"📁 Fichier temporaire créé: {temp_file_path} (format: {detected_format})")
        return temp_file_path, detected_format

    def speech_to_text_from_bytes(self, audio_bytes: bytes) -> Optional[str]:
        """
        Convertit un audio en bytes vers du texte
        
        Args:
            audio_bytes: Audio en format bytes
            
        Returns:
            Texte transcrit ou None si erreur
        """
        try:
            # Créer un fichier temporaire avec l'extension appropriée
            temp_file_path, detected_format = self._create_temp_file_with_extension(audio_bytes)
            
            try:
                callback = None
                stream = None
                speech_recognizer = None
                
                # Configuration pour formats compressés (WebM, OGG, MP3, M4A) et WAV
                if detected_format in ['webm', 'ogg', 'mp3', 'm4a']:
                    # Utiliser le support natif Azure Speech Service pour formats compressés
                    logger.info(f"🔧 Configuration format compressé pour {detected_format.upper()}")
                    
                    # Créer un format audio compressé - Azure Speech Service supporte nativement WebM/OGG via GStreamer
                    compressed_format = speechsdk.audio.AudioStreamFormat(compressed_stream_format=speechsdk.AudioStreamContainerFormat.ANY)
                    
                    # Créer un stream d'entrée pour le format compressé
                    callback = BinaryFileReaderCallback(temp_file_path)
                    stream = speechsdk.audio.PullAudioInputStream(callback, compressed_format)
                    audio_config = speechsdk.audio.AudioConfig(stream=stream)
                    
                else:
                    # Configuration standard pour WAV
                    logger.info("🔧 Configuration standard pour WAV")
                    audio_config = speechsdk.audio.AudioConfig(filename=temp_file_path)
                
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self._speech_config,
                    audio_config=audio_config
                )
                
                # Reconnaissance vocale
                logger.info(f"🎤 Début reconnaissance vocale ({detected_format})...")
                result = speech_recognizer.recognize_once_async().get()
                
                # Fermer les ressources avant de traiter le résultat
                if stream:
                    stream.close()
                if callback:
                    callback.close()
                if speech_recognizer:
                    del speech_recognizer
                
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    logger.info(f"✅ Texte reconnu: {result.text[:50]}...")
                    return result.text.strip()
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    logger.warning("⚠️ Aucun speech reconnu dans l'audio")
                    return None
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    logger.error(f"❌ Reconnaissance annulée: {cancellation_details.reason}")
                    if cancellation_details.reason == speechsdk.CancellationReason.Error:
                        logger.error(f"❌ Détails erreur: {cancellation_details.error_details}")
                    return None
                else:
                    logger.error(f"❌ Erreur reconnaissance: {result.reason}")
                    return None
                    
            finally:
                # S'assurer que toutes les ressources sont fermées avant de supprimer le fichier
                try:
                    if 'stream' in locals() and stream:
                        stream.close()
                    if 'callback' in locals() and callback:
                        callback.close()
                    if 'speech_recognizer' in locals() and speech_recognizer:
                        del speech_recognizer
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Erreur nettoyage ressources: {cleanup_error}")
                
                # Nettoyer le fichier temporaire avec retry pour les verrous de fichier
                import time
                for attempt in range(3):
                    try:
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                        break
                    except (OSError, PermissionError) as e:
                        if attempt < 2:  # Retry pour les 2 premiers essais
                            logger.warning(f"⚠️ Tentative {attempt+1} suppression fichier échouée: {e}")
                            time.sleep(0.1)  # Attendre 100ms avant de retry
                        else:
                            logger.error(f"❌ Impossible de supprimer le fichier temporaire: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Erreur speech-to-text: {e}")
            return None
    
    def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convertit du texte en audio (bytes)
        
        Args:
            text: Texte à synthétiser
            
        Returns:
            Audio en bytes ou None si erreur
        """
        try:
            if not text or not text.strip():
                logger.warning("⚠️ Texte vide pour TTS")
                return None
                
            logger.info(f"🔊 Synthèse vocale: {text[:50]}...")
            
            # Configuration audio en mémoire
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self._speech_config,
                audio_config=audio_config
            )
            
            # Synthèse vocale
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("✅ Synthèse vocale réussie")
                return result.audio_data
            else:
                logger.error(f"❌ Erreur synthèse: {result.cancellation_details}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur text-to-speech: {e}")
            return None
    
    def text_to_speech_base64(self, text: str) -> Optional[str]:
        """
        Convertit du texte en audio encodé base64 (pour Streamlit)
        
        Args:
            text: Texte à synthétiser
            
        Returns:
            Audio encodé en base64 ou None si erreur
        """
        audio_bytes = self.text_to_speech(text)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None
    
    def is_available(self) -> bool:
        """Vérifie si le service Azure Speech est disponible"""
        return (
            self._speech_config is not None and 
            self.settings.azure_speech_key is not None
        )
    
    def get_status(self) -> dict:
        """Retourne le statut du service audio"""
        return {
            "azure_speech_available": self.is_available(),
            "speech_key_configured": bool(self.settings.azure_speech_key),
            "region": self.settings.azure_speech_region,
            "recognition_language": "fr-FR",
            "synthesis_voice": "fr-FR-DeniseNeural"
        }