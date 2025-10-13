import json
import os

class UniversalEngineSettings:
    """Gestionnaire des paramètres pour tous les moteurs UCI"""

    def __init__(self, config_file="engine_settings.json"):
        self.config_file = config_file

        # Paramètres communs à tous les moteurs UCI
        self.universal_options = {
            "threads": {"min": 1, "max": 16, "default": 1, "description": "Nombre de threads CPU"},
            "hash": {"min": 1, "max": 2048, "default": 64, "description": "Mémoire Hash (MB)"},
            "time_limit": {"min": 0.1, "max": 10.0, "default": 5.0, "description": "Temps max par coup (s)"},
            "depth_limit": {"min": 0, "max": 50, "default": 0, "description": "Profondeur max (0=illimité)"}
        }

        # Paramètres spécifiques à Stockfish
        self.stockfish_options = {
            "skill_level": {"min": 0, "max": 20, "default": 15, "description": "Niveau de jeu"},
            "move_overhead": {"min": 0, "max": 1000, "default": 10, "description": "Compensation lag (ms)"}
        }

        # Paramètres spécifiques à Leela Chess Zero
        self.leela_options = {
            "nodes": {"min": 1, "max": 100000, "default": 1000, "description": "Noeuds par coup"},
            "temperature": {"min": 0.0, "max": 2.0, "default": 0.0, "description": "Température (créativité)"}
        }

        # Conversion ELO approximative pour différents moteurs
        self.elo_mappings = {
            "stockfish": {
                0: 1350, 1: 1400, 2: 1450, 3: 1500, 4: 1550,
                5: 1600, 6: 1650, 7: 1700, 8: 1800, 9: 1900,
                10: 2000, 11: 2100, 12: 2200, 13: 2300, 14: 2400,
                15: 2500, 16: 2600, 17: 2700, 18: 2850, 19: 3000, 20: 3200
            },
            "other": {  # Pour les autres moteurs, mapping plus granulaire
                0: 1400, 1: 1500, 2: 1600, 3: 1700, 4: 1800, 5: 1900,
                6: 2000, 7: 2100, 8: 2200, 9: 2300, 10: 2400, 11: 2500,
                12: 2600, 13: 2700, 14: 2800, 15: 2900, 16: 3000, 17: 3100,
                18: 3200, 19: 3300, 20: 3400
            }
        }

        self.settings = self.load_settings()

    def get_selected_engine(self):
        """Retourne le moteur actuellement sélectionné"""
        try:
            with open("selected_engine.txt", "r") as f:
                return f.read().strip()
        except:
            return "legacy_stockfish"

    def get_engine_type(self, engine_id=None):
        """Détermine le type de moteur pour adapter les paramètres"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        if "stockfish" in engine_id.lower():
            return "stockfish"
        elif "leela" in engine_id.lower() or "lc0" in engine_id.lower():
            return "leela"
        else:
            return "other"

    def get_available_options(self, engine_id=None):
        """Retourne les options disponibles pour un moteur"""
        engine_type = self.get_engine_type(engine_id)

        options = self.universal_options.copy()

        if engine_type == "stockfish":
            options.update(self.stockfish_options)

        return options

    def load_settings(self):
        """Charge les paramètres depuis le fichier JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des paramètres : {e}")

        # Paramètres par défaut
        return {
            "engines": {},
            "global": {
                "threads": 1,
                "hash": 64,
                "time_limit": 1.0,
                "depth_limit": 0
            }
        }

    def save_settings(self):
        """Sauvegarde les paramètres dans le fichier JSON"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
            return False

    def get_engine_settings(self, engine_id=None):
        """Retourne les paramètres pour un moteur spécifique"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        # Paramètres globaux par défaut
        settings = self.settings["global"].copy()

        # Paramètres spécifiques au moteur s'ils existent
        if engine_id in self.settings.get("engines", {}):
            settings.update(self.settings["engines"][engine_id])

        # Ajouter les paramètres par défaut manquants selon le type de moteur
        available_options = self.get_available_options(engine_id)
        for option, config in available_options.items():
            if option not in settings:
                settings[option] = config["default"]

        return settings

    def set_engine_setting(self, option, value, engine_id=None):
        """Définit un paramètre pour un moteur"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        if "engines" not in self.settings:
            self.settings["engines"] = {}

        if engine_id not in self.settings["engines"]:
            self.settings["engines"][engine_id] = {}

        self.settings["engines"][engine_id][option] = value

        # Aussi mettre à jour les paramètres globaux pour les options communes
        if option in self.universal_options:
            self.settings["global"][option] = value

    def get_elo_range_for_engine(self, engine_id=None):
        """Retourne la plage ELO disponible pour un moteur"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        engine_type = self.get_engine_type(engine_id)

        if engine_type == "stockfish":
            elos = list(self.elo_mappings["stockfish"].values())
        elif engine_type == "leela":
            elos = list(self.elo_mappings["leela"].values())
        else:
            elos = list(self.elo_mappings["other"].values())

        return min(elos), max(elos)

    def get_elo_for_engine(self, engine_id=None):
        """Retourne l'ELO approximatif pour le moteur"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        engine_type = self.get_engine_type(engine_id)
        settings = self.get_engine_settings(engine_id)

        # Vérifier si on a un niveau ELO stocké
        if "elo_level" in settings:
            return self.get_elo_from_level(settings["elo_level"], engine_type)

        # Sinon, calculer depuis les autres paramètres
        if engine_type == "stockfish" and "skill_level" in settings:
            skill_level = settings["skill_level"]
            return self.elo_mappings["stockfish"].get(skill_level, 2000)
        else:
            # Pour les autres moteurs, utiliser un niveau moyen par défaut
            if engine_type == "leela":
                return self.elo_mappings["leela"].get(8, 2800)  # Niveau moyen
            else:
                return self.elo_mappings["other"].get(10, 2400)  # Niveau moyen

    def get_elo_from_level(self, level, engine_type):
        """Convertit un niveau en ELO selon le type de moteur"""
        if engine_type == "stockfish":
            return self.elo_mappings["stockfish"].get(level, 2000)
        elif engine_type == "leela":
            return self.elo_mappings["leela"].get(level, 2800)
        else:
            return self.elo_mappings["other"].get(level, 2400)

    def set_elo_for_engine(self, target_elo, engine_id=None):
        """Ajuste les paramètres pour atteindre l'ELO cible"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        engine_type = self.get_engine_type(engine_id)

        if engine_type == "stockfish":
            # Pour Stockfish, ajuster le skill level
            closest_skill = min(self.elo_mappings["stockfish"].keys(),
                              key=lambda k: abs(self.elo_mappings["stockfish"][k] - target_elo))
            self.set_engine_setting("skill_level", closest_skill, engine_id)
            self.set_engine_setting("elo_level", closest_skill, engine_id)
        elif engine_type == "leela":
            # Pour Leela, trouver le niveau le plus proche
            closest_level = min(self.elo_mappings["leela"].keys(),
                              key=lambda k: abs(self.elo_mappings["leela"][k] - target_elo))
            self.set_engine_setting("elo_level", closest_level, engine_id)
            # Ajuster les paramètres techniques pour Leela
            if target_elo < 2500:
                self.set_engine_setting("nodes", 500, engine_id)
                self.set_engine_setting("time_limit", 0.5, engine_id)
            elif target_elo < 3000:
                self.set_engine_setting("nodes", 1000, engine_id)
                self.set_engine_setting("time_limit", 1.0, engine_id)
            else:
                self.set_engine_setting("nodes", 2000, engine_id)
                self.set_engine_setting("time_limit", 2.0, engine_id)
        else:
            # Pour les autres moteurs, utiliser le mapping "other"
            closest_level = min(self.elo_mappings["other"].keys(),
                              key=lambda k: abs(self.elo_mappings["other"][k] - target_elo))
            self.set_engine_setting("elo_level", closest_level, engine_id)
            # Ajuster le temps et la profondeur selon le niveau
            if target_elo < 2000:
                self.set_engine_setting("time_limit", 0.3, engine_id)
                self.set_engine_setting("depth_limit", 8, engine_id)
            elif target_elo < 2500:
                self.set_engine_setting("time_limit", 0.5, engine_id)
                self.set_engine_setting("depth_limit", 12, engine_id)
            elif target_elo < 3000:
                self.set_engine_setting("time_limit", 1.0, engine_id)
                self.set_engine_setting("depth_limit", 0, engine_id)
            else:
                self.set_engine_setting("time_limit", 2.0, engine_id)
                self.set_engine_setting("depth_limit", 0, engine_id)

    def get_uci_config(self, engine_id=None):
        """Retourne la configuration UCI pour un moteur"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        settings = self.get_engine_settings(engine_id)
        engine_type = self.get_engine_type(engine_id)

        uci_config = {}

        # Options communes
        if "threads" in settings:
            uci_config["Threads"] = settings["threads"]
        if "hash" in settings:
            uci_config["Hash"] = settings["hash"]

        # Options spécifiques à Stockfish
        if engine_type == "stockfish":
            if "skill_level" in settings:
                uci_config["Skill Level"] = settings["skill_level"]
            if "move_overhead" in settings:
                uci_config["Move Overhead"] = settings["move_overhead"]

        # Options spécifiques à Leela
        elif engine_type == "leela":
            if "nodes" in settings:
                uci_config["Nodes"] = settings["nodes"]
            if "temperature" in settings:
                uci_config["Temperature"] = settings["temperature"]

            # Ajouter le chemin vers le fichier weights pour Leela
            from engine_manager import EngineManager
            engine_manager = EngineManager()
            if engine_manager.is_engine_installed(engine_id):
                engine_dir = engine_manager.engines_dir / engine_id
                weights_file = engine_dir / "BT4-1024x15x32h-swa-6147500.pb.gz"
                if weights_file.exists():
                    uci_config["WeightsFile"] = str(weights_file)

        return uci_config

    def get_search_limits(self, engine_id=None):
        """Retourne les limites de recherche pour un moteur"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        settings = self.get_engine_settings(engine_id)
        limits = {}

        if settings.get("time_limit", 0) > 0:
            limits["time"] = settings["time_limit"]
        if settings.get("depth_limit", 0) > 0:
            limits["depth"] = settings["depth_limit"]

        # Si aucune limite, utiliser un temps par défaut
        if not limits:
            limits["time"] = 1.0

        return limits

    def reset_engine_to_defaults(self, engine_id=None):
        """Remet les paramètres d'un moteur aux valeurs par défaut"""
        if not engine_id:
            engine_id = self.get_selected_engine()

        if "engines" in self.settings and engine_id in self.settings["engines"]:
            del self.settings["engines"][engine_id]

        self.save_settings()