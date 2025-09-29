import json
import os

class StockfishSettings:
    """Gestionnaire des paramètres Stockfish"""
    
    # Conversion approximative Skill Level → ELO
    SKILL_TO_ELO = {
        0: 1350, 1: 1400, 2: 1450, 3: 1500, 4: 1550,
        5: 1600, 6: 1650, 7: 1700, 8: 1800, 9: 1900,
        10: 2000, 11: 2100, 12: 2200, 13: 2300, 14: 2400,
        15: 2500, 16: 2600, 17: 2700, 18: 2850, 19: 3000,
        20: 3200
    }
    
    def __init__(self, config_file="stockfish_config.json"):
        self.config_file = config_file
        
        # Paramètres par défaut
        self.default_settings = {
            "skill_level": 15,      # 0-20 (20 = max)
            "threads": 1,           # 1-128
            "hash": 64,             # MB (1-33554432)
            "time_limit": 0.5,      # secondes (0 = illimité)
            "depth_limit": 0,       # coups (0 = illimité)
            "move_overhead": 10,    # ms (compensation lag réseau)
            # Options retirées car non universelles ou gérées automatiquement :
            # - MultiPV, Ponder : gérés par python-chess
            # - Contempt, Minimum Thinking Time, Slow Mover : anciennes versions seulement
        }
        
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Charge les paramètres depuis le fichier JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Fusionner avec les valeurs par défaut
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
            except Exception as e:
                print(f"Erreur lors du chargement des paramètres : {e}")
                return self.default_settings.copy()
        return self.default_settings.copy()
    
    def save_settings(self):
        """Sauvegarde les paramètres dans le fichier JSON"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
            return False
    
    def get_elo(self):
        """Retourne l'ELO approximatif basé sur le Skill Level"""
        skill = self.settings["skill_level"]
        return self.SKILL_TO_ELO.get(skill, 2000)
    
    def set_elo(self, target_elo):
        """Définit le Skill Level basé sur l'ELO cible"""
        # Trouver le skill level le plus proche
        closest_skill = min(self.SKILL_TO_ELO.keys(), 
                          key=lambda k: abs(self.SKILL_TO_ELO[k] - target_elo))
        self.settings["skill_level"] = closest_skill
    
    def get_engine_config(self):
        """Retourne la configuration pour le moteur UCI
        
        Note: Seules les options universellement supportées sont incluses.
        MultiPV et Ponder sont gérés automatiquement par python-chess.
        Contempt, Minimum Thinking Time, Slow Mover ne sont plus dans Stockfish 16+.
        """
        return {
            "Threads": self.settings["threads"],
            "Hash": self.settings["hash"],
            "Skill Level": self.settings["skill_level"],
            "Move Overhead": self.settings.get("move_overhead", 10)
        }
    
    def get_search_limit(self):
        """Retourne les limites de recherche"""
        limits = {}
        if self.settings["time_limit"] > 0:
            limits["time"] = self.settings["time_limit"]
        if self.settings["depth_limit"] > 0:
            limits["depth"] = self.settings["depth_limit"]
        # Si aucune limite, utiliser un temps par défaut
        if not limits:
            limits["time"] = 1.0
        return limits
    
    def reset_to_defaults(self):
        """Réinitialise aux paramètres par défaut"""
        self.settings = self.default_settings.copy()
        self.save_settings()