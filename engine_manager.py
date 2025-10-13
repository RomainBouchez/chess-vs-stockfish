import os
import json
import requests
import zipfile
import platform
import shutil
from urllib.parse import urlparse
from pathlib import Path

class EngineManager:
    """Gestionnaire des moteurs d'échecs téléchargeables"""
    
    def __init__(self, engines_dir="engines"):
        self.engines_dir = Path(engines_dir)
        self.engines_dir.mkdir(exist_ok=True)
        self.config_file = "engines_config.json"
        
        # Configuration des moteurs disponibles
        self.available_engines = {
            "stockfish_latest": {
                "name": "Stockfish latest",
                "description": "Moteur d'échecs le plus fort au monde",
                "version": "latest",
                "urls": {
                    "windows": "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip",
                    "linux": "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2.tar",
                    "mac": "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-macos-x86-64-avx2.tar"
                },
                "executable": {
                    "windows": "stockfish-windows-x86-64-avx2.exe",
                    "linux": "stockfish",
                    "mac": "stockfish"
                }
            },
            # "leela_chess_zero": {
            #     "name": "Leela Chess Zero",
            #     "description": "Moteur neuronal open-source inspiré d'AlphaZero",
            #     "version": "0.32.0",
            #     "urls": {
            #         "windows": "https://github.com/LeelaChessZero/lc0/releases/download/v0.32.0/lc0-v0.32.0-windows-cpu-openblas.zip"
            #     },
            #     "executable": {
            #         "windows": "lc0.exe",
            #         "linux": "lc0",
            #         "mac": "lc0"
            #     },
            #     "weights_url": "https://storage.lczero.org/get/networks/bestnets/BT4-1024x15x32h-swa-6147500.pb.gz",
            #     "weights_file": "BT4-1024x15x32h-swa-6147500.pb.gz",
            #     "special_setup": "leela"
            # },
            # "rubichess": {
            #     "name": "RubiChess",
            #     "description": "Moteur allemand fort et moderne",
            #     "version": "20240817",
            #     "urls": {
            #         "windows": "https://github.com/Matthies/RubiChess/releases/download/20240817/RubiChess-20240817.zip"
            #     },
            #     "executable": {
            #         "windows": "RubiChess-20240817-win64-modern.exe",
            #         "linux": "rubichess",
            #         "mac": "rubichess"
            #     }
            # },
            # "berserk": {
            #     "name": "Berserk",
            #     "description": "Moteur rapide et agressif",
            #     "version": "13",
            #     "urls": {
            #         "windows": "https://github.com/jhonnold/berserk/releases/download/13/berserk-13-x86-64.exe"
            #     },
            #     "executable": {
            #         "windows": "berserk-13-x86_64-windows.exe",
            #         "linux": "berserk",
            #         "mac": "berserk"
            #     }
            # },
            # "igel": {
            #     "name": "Igel",
            #     "description": "Moteur UCI moderne avec NNUE",
            #     "version": "3.5.5",
            #     "urls": {
            #         "windows": "https://github.com/vshcherbyna/igel/releases/download/3.6.0/igel-x64_bmi2_avx2_3_6_0.exe"
            #     },
            #     "executable": {
            #         "windows": "igel-v3.5.5-64bit.exe",
            #         "linux": "igel",
            #         "mac": "igel"
            #     }
            # },
            # "koivisto": {
            #     "name": "Koivisto",
            #     "description": "Moteur finlandais rapide avec NNUE",
            #     "version": "9.0",
            #     "urls": {
            #         "windows": "https://github.com/Luecx/Koivisto/releases/download/v9.0/Koivisto_9.0-windows-avx2-pgo.exe"
            #     },
            #     "executable": {
            #         "windows": "Koivisto_9.0_windows.exe",
            #         "linux": "koivisto",
            #         "mac": "koivisto"
            #     }
            # }
        }
        
        self.installed_engines = self.load_installed_engines()
        
    def get_platform(self):
        """Détecte la plateforme actuelle"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            return "linux" 
        elif system == "darwin":
            return "mac"
        else:
            return "linux"  # Par défaut
            
    def load_installed_engines(self):
        """Charge la liste des moteurs installés"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des moteurs installés: {e}")
        return {}
        
    def save_installed_engines(self):
        """Sauvegarde la liste des moteurs installés"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.installed_engines, f, indent=4)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False
            
    def get_available_engines(self):
        """Retourne la liste des moteurs disponibles au téléchargement"""
        return self.available_engines
        
    def get_installed_engines(self):
        """Retourne la liste des moteurs installés"""
        return self.installed_engines
        
    def is_engine_installed(self, engine_id):
        """Vérifie si un moteur est installé"""
        return engine_id in self.installed_engines
        
    def get_engine_path(self, engine_id):
        """Retourne le chemin vers l'exécutable du moteur"""
        if not self.is_engine_installed(engine_id):
            return None
            
        engine_info = self.installed_engines[engine_id]
        return engine_info.get("path")
        
    def download_engine(self, engine_id, progress_callback=None):
        """Télécharge et installe un moteur"""
        if engine_id not in self.available_engines:
            raise ValueError(f"Moteur {engine_id} non disponible")
            
        if self.is_engine_installed(engine_id):
            raise ValueError(f"Moteur {engine_id} déjà installé")
            
        engine_config = self.available_engines[engine_id]
        platform_name = self.get_platform()
        
        if platform_name not in engine_config["urls"]:
            raise ValueError(f"Moteur {engine_id} non disponible pour {platform_name}")
            
        url = engine_config["urls"][platform_name]
        executable_name = engine_config["executable"][platform_name]
        
        # Créer le dossier du moteur
        engine_dir = self.engines_dir / engine_id
        engine_dir.mkdir(exist_ok=True)
        
        try:
            # Télécharger le fichier
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = f"{engine_id}.{url.split('.')[-1]}"
                
            download_path = engine_dir / filename
            
            print(f"Téléchargement de {engine_config['name']} depuis {url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
                            
            # Extraire l'archive
            if filename.endswith('.zip'):
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(engine_dir)
            elif filename.endswith(('.tar', '.tar.gz')):
                import tarfile
                with tarfile.open(download_path, 'r:*') as tar_ref:
                    tar_ref.extractall(engine_dir)
                    
            # Trouver l'exécutable
            executable_path = None

            # Première passe: chercher l'exécutable exact
            for root, dirs, files in os.walk(engine_dir):
                for file in files:
                    if file == executable_name:
                        executable_path = os.path.join(root, file)
                        print(f"Exécutable trouvé (nom exact): {executable_path}")
                        break
                if executable_path:
                    break

            # Deuxième passe: chercher par nom partiel
            if not executable_path:
                base_name = executable_name.split('.')[0]
                for root, dirs, files in os.walk(engine_dir):
                    for file in files:
                        if file.startswith(base_name) and (platform_name == "windows" and file.endswith('.exe')):
                            executable_path = os.path.join(root, file)
                            print(f"Exécutable trouvé (nom partiel): {executable_path}")
                            break
                    if executable_path:
                        break

            # Troisième passe: chercher n'importe quel exécutable (pour moteurs avec noms différents)
            if not executable_path:
                print(f"Recherche de n'importe quel exécutable dans {engine_dir}")
                for root, dirs, files in os.walk(engine_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        if platform_name == "windows" and file.endswith('.exe'):
                            # Vérifier que ce n'est pas un installateur
                            if not any(word in file.lower() for word in ['setup', 'install', 'uninstall']):
                                executable_path = full_path
                                print(f"Exécutable trouvé (fallback): {executable_path}")
                                break
                        elif platform_name != "windows" and os.access(full_path, os.X_OK):
                            executable_path = full_path
                            print(f"Exécutable trouvé (fallback): {executable_path}")
                            break
                    if executable_path:
                        break
                        
            if not executable_path:
                raise Exception(f"Exécutable non trouvé pour {engine_id}")
                
            # Rendre exécutable sur Unix
            if platform_name != "windows":
                os.chmod(executable_path, 0o755)
                
            # Supprimer l'archive téléchargée
            os.remove(download_path)

            # Gestion spéciale pour Leela Chess Zero
            if engine_config.get("special_setup") == "leela":
                print("Configuration spéciale pour Leela Chess Zero...")
                weights_url = engine_config.get("weights_url")
                weights_file = engine_config.get("weights_file")

                if weights_url and weights_file:
                    print(f"Téléchargement du réseau neuronal: {weights_file}")
                    weights_path = engine_dir / weights_file

                    try:
                        # Télécharger le fichier weights
                        response = requests.get(weights_url, stream=True)
                        response.raise_for_status()

                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0

                        with open(weights_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if progress_callback and total_size > 0:
                                        progress = 50 + (downloaded / total_size) * 50  # 50-100%
                                        progress_callback(progress)

                        print(f"Réseau neuronal téléchargé: {weights_path}")

                    except Exception as e:
                        print(f"Erreur lors du téléchargement du réseau neuronal: {e}")
                        # Continuer quand même l'installation

            # Enregistrer l'installation
            self.installed_engines[engine_id] = {
                "name": engine_config["name"],
                "version": engine_config["version"],
                "path": executable_path,
                "installed_date": str(Path().resolve())  # Date d'installation simplifiée
            }
            
            self.save_installed_engines()
            print(f"{engine_config['name']} installé avec succès!")
            return True
            
        except Exception as e:
            # Nettoyer en cas d'erreur
            if engine_dir.exists():
                shutil.rmtree(engine_dir)
            raise Exception(f"Erreur lors de l'installation de {engine_id}: {e}")
            
    def uninstall_engine(self, engine_id):
        """Désinstalle un moteur"""
        if not self.is_engine_installed(engine_id):
            raise ValueError(f"Moteur {engine_id} non installé")
            
        engine_dir = self.engines_dir / engine_id
        if engine_dir.exists():
            shutil.rmtree(engine_dir)
            
        del self.installed_engines[engine_id]
        self.save_installed_engines()
        print(f"Moteur {engine_id} désinstallé")
        return True
        
    def verify_engine(self, engine_id):
        """Vérifie qu'un moteur installé fonctionne"""
        if not self.is_engine_installed(engine_id):
            return False
            
        path = self.get_engine_path(engine_id)
        if not path or not os.path.exists(path):
            return False
            
        try:
            # Test simple UCI
            import subprocess
            process = subprocess.Popen([path], stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True)
            stdout, stderr = process.communicate(input="uci\nquit\n", timeout=5)
            return "uciok" in stdout.lower()
        except:
            return False
            
    def get_default_engine(self):
        """Retourne le moteur par défaut (le premier installé)"""
        if not self.installed_engines:
            return None
        return list(self.installed_engines.keys())[0]

    def repair_engine(self, engine_id):
        """Répare un moteur en cherchant l'exécutable correct"""
        if engine_id not in self.installed_engines:
            return False

        engine_dir = self.engines_dir / engine_id
        if not engine_dir.exists():
            return False

        print(f"🔧 Réparation de {engine_id}...")

        # Chercher tous les exécutables
        platform_name = self.get_platform()
        executable_candidates = []

        for root, dirs, files in os.walk(engine_dir):
            for file in files:
                full_path = os.path.join(root, file)
                if platform_name == "windows" and file.endswith('.exe'):
                    # Éviter les installateurs
                    if not any(word in file.lower() for word in ['setup', 'install', 'uninstall']):
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        executable_candidates.append((full_path, size_mb))
                elif platform_name != "windows" and os.access(full_path, os.X_OK):
                    size_mb = os.path.getsize(full_path) / (1024 * 1024)
                    executable_candidates.append((full_path, size_mb))

        if not executable_candidates:
            print(f"❌ Aucun exécutable trouvé pour {engine_id}")
            return False

        # Prendre le plus gros exécutable (probablement le moteur principal)
        executable_candidates.sort(key=lambda x: x[1], reverse=True)
        best_executable = executable_candidates[0][0]

        print(f"✅ Exécutable trouvé: {best_executable}")

        # Mettre à jour la configuration
        self.installed_engines[engine_id]["path"] = best_executable
        self.save_installed_engines()

        # Tester l'exécutable
        if self.verify_engine(engine_id):
            print(f"✅ {engine_id} réparé avec succès!")
            return True
        else:
            print(f"❌ {engine_id} ne répond pas correctement")
            return False