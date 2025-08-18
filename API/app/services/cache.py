from typing import Dict, Any, Optional

class GameCache:
    def __init__(self):
        self.analyses = {} # Stockage en mémoire
        
    def store_analysis(self, game_id: str, analysis: Dict[str, Any]):
        """Stocke une analyse de jeu"""
        self.analyses[game_id] = analysis
        
    def get_analysis(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une analyse par game_id"""
        return self.analyses.get(game_id)
    
    def exists(self, game_id: str) -> bool:
        """Vérifie si un game_id existe"""
        return game_id in self.analyses
    
# Instance globale du cache
game_cache = GameCache()