from abc import ABC, abstractmethod


class IPasswordService(ABC):
    """Interface pour les services de gestion des mots de passe"""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hache un mot de passe"""
        pass

    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Vérifie un mot de passe contre son hash"""
        pass