import sys
import os
import chess
import chess.engine
from settings import StockfishSettings
from universal_settings import UniversalEngineSettings
from engine_manager import EngineManager

class UniversalEngine:
    """Interface universelle pour les moteurs d'échecs UCI"""
    
    def __init__(self):
        self.engine = None
        self.engine_path = None
        self.engine_name = None
        self.settings = StockfishSettings()  # Garder pour compatibilité
        self.universal_settings = UniversalEngineSettings()
        self.engine_manager = EngineManager()
    
    def get_selected_engine_path(self):
        """Récupère le chemin du moteur sélectionné"""
        try:
            # Lire le moteur sélectionné
            with open("selected_engine.txt", "r") as f:
                selected_engine = f.read().strip()
                #print engine path for debug
                
            
            # Obtenir le chemin via l'engine manager
            engine_path = self.engine_manager.get_engine_path(selected_engine)
            if engine_path and os.path.exists(engine_path):
                return engine_path, selected_engine
        except:
            pass
        
        # Fallback vers l'ancien chemin par défaut
        fallback_path = r"C:\Users\romai\Documents\1._Romain\2_Esiea\4A\PST\dist\ystockfish.exe"
        if os.path.exists(fallback_path):
            return fallback_path, "legacy_stockfish"
        
        return None, None
    
    def auto_install_engine(self):
        """Essaie d'installer automatiquement un moteur si aucun n'est disponible"""
        try:
            available = self.engine_manager.get_available_engines()
            
            # Essayer d'installer Stockfish 16 en priorité
            if "stockfish_16" in available:
                print("Installation automatique de Stockfish 16...")
                self.engine_manager.download_engine("stockfish_16")
                
                # Sauvegarder comme moteur sélectionné
                with open("selected_engine.txt", "w") as f:
                    f.write("stockfish_16")
                
                return self.engine_manager.get_engine_path("stockfish_16"), "stockfish_16"
        except Exception as e:
            print(f"Impossible d'installer automatiquement un moteur: {e}")
        
        return None, None
    
    def initialize(self):
        """Initialise le moteur sélectionné"""
        if self.engine:
            return True
            
        # Obtenir le chemin du moteur
        self.engine_path, self.engine_name = self.get_selected_engine_path()
        
        if not self.engine_path:
            print("Aucun moteur disponible. Tentative d'installation automatique...")
            self.engine_path, self.engine_name = self.auto_install_engine()
        
        if not self.engine_path:
            print("[ERREUR] Aucun moteur d'échecs disponible.")
            print("Veuillez installer un moteur via le menu Paramètres > Moteurs")
            return False
        
        print(f"Initialisation du moteur: {self.engine_name} ({self.engine_path})")
        
        if not os.path.isfile(self.engine_path):
            print(f"[ERREUR] Moteur introuvable à : {self.engine_path}")
            return False
        
        try:
            # Lancer le moteur
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            # Appliquer la configuration universelle
            engine_config = self.universal_settings.get_uci_config(self.engine_name)
            print(f"Configuration moteur : {engine_config}")

            # Appliquer seulement les options supportées
            supported_config = {}
            for option, value in engine_config.items():
                try:
                    if option in self.engine.options:
                        supported_config[option] = value
                    else:
                        print(f"Option '{option}' non supportée par ce moteur")
                except:
                    pass

            if supported_config:
                self.engine.configure(supported_config)
                print(f"Configuration appliquée: {supported_config}")

            # Afficher l'ELO approximatif
            elo = self.universal_settings.get_elo_for_engine(self.engine_name)
            print(f"ELO approximatif : {elo}")
            
            return True
            
        except Exception as e:
            print(f"[ERREUR] Impossible de lancer le moteur : {e}")
            if self.engine:
                try:
                    self.engine.quit()
                except:
                    pass
                self.engine = None
            return False
    
    def get_best_move(self, fen):
        """Obtient le meilleur coup pour une position FEN donnée"""
        if not self.engine and not self.initialize():
            return None

        try:
            board = chess.Board(fen)

            # Vérifier que la position est valide
            if not board.is_valid():
                print(f"[ERREUR] Position FEN invalide : {fen}")
                return None

            # Obtenir les limites de recherche depuis les paramètres universels
            search_limits = self.universal_settings.get_search_limits(self.engine_name)

            # Créer l'objet Limit
            limit_kwargs = {}
            if "time" in search_limits:
                limit_kwargs["time"] = search_limits["time"]
            if "depth" in search_limits:
                limit_kwargs["depth"] = search_limits["depth"]

            limit = chess.engine.Limit(**limit_kwargs)

            # Demander le meilleur coup
            result = self.engine.play(board, limit)

            if result.move is None:
                print("[ERREUR] Le moteur n'a pas trouvé de coup")
                return None

            bestmove_uci = result.move.uci()

            # Écrire le coup dans bestmove.txt pour le robot
            try:
                with open("bestmove.txt", "w") as f:
                    f.write(bestmove_uci)
                print(f"[INFO] Coup écrit dans bestmove.txt: {bestmove_uci}")
            except Exception as e:
                print(f"[AVERTISSEMENT] Impossible d'écrire dans bestmove.txt: {e}")

            return bestmove_uci
            
        except chess.engine.EngineTerminatedError:
            print("[ERREUR] Le moteur s'est arrêté de manière inattendue")
            self.engine = None
            return None
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'analyse : {e}")
            return None
    
    def is_available(self):
        """Vérifie si un moteur est disponible"""
        return self.engine is not None or self.get_selected_engine_path()[0] is not None
    
    def get_engine_info(self):
        """Retourne les informations sur le moteur actuel"""
        if not self.engine_name:
            self.engine_path, self.engine_name = self.get_selected_engine_path()
        
        return {
            "name": self.engine_name,
            "path": self.engine_path,
            "available": self.is_available()
        }
    
    def quit(self):
        """Ferme le moteur proprement"""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
            self.engine = None
    
    def __del__(self):
        """Destructeur pour s'assurer que le moteur se ferme"""
        self.quit()

# Instance globale pour faciliter l'utilisation
_universal_engine = None

def get_universal_engine():
    """Retourne l'instance globale du moteur universel"""
    global _universal_engine
    if _universal_engine is None:
        _universal_engine = UniversalEngine()
    return _universal_engine