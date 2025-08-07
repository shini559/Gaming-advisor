import sys
import io
import contextlib
from datetime import datetime
from typing import List, Dict
import streamlit as st


class LogCapture:
    """Capture et stockage des logs pour affichage dans Streamlit"""
    
    def __init__(self):
        self.logs = []
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.is_capturing = False
    
    def start_capture(self):
        """Démarre la capture des prints et logs"""
        if not self.is_capturing:
            sys.stdout = LogBuffer(self.original_stdout, self._add_log)
            sys.stderr = LogBuffer(self.original_stderr, self._add_log, is_error=True)
            self.is_capturing = True
    
    def stop_capture(self):
        """Arrête la capture des logs"""
        if self.is_capturing:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            self.is_capturing = False
    
    def _add_log(self, message: str, is_error: bool = False):
        """Ajoute un log à la liste avec timestamp"""
        if message.strip():  # Ignorer les lignes vides
            log_entry = {
                "timestamp": datetime.now(),
                "message": message.strip(),
                "is_error": is_error
            }
            self.logs.append(log_entry)
            
            # Limiter à 1000 logs pour éviter l'accumulation
            if len(self.logs) > 1000:
                self.logs = self.logs[-1000:]
    
    def get_logs(self) -> List[Dict]:
        """Retourne la liste des logs"""
        return self.logs.copy()
    
    def clear_logs(self):
        """Vide les logs"""
        self.logs.clear()
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Retourne les logs récents"""
        return self.logs[-limit:] if len(self.logs) > limit else self.logs


class LogBuffer(io.StringIO):
    """Buffer personnalisé pour capturer les outputs"""
    
    def __init__(self, original_stream, log_callback, is_error=False):
        super().__init__()
        self.original_stream = original_stream
        self.log_callback = log_callback
        self.is_error = is_error
    
    def write(self, message):
        # Écrire dans le stream original
        self.original_stream.write(message)
        self.original_stream.flush()
        
        # Capturer pour les logs
        if message and message.strip():
            self.log_callback(message, self.is_error)
        
        return len(message)
    
    def flush(self):
        self.original_stream.flush()


# Instance globale du log capture
log_capture = LogCapture()