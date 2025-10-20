import serial
import time
import os
import configparser
from threading import Thread, Event
from typing import Tuple, Optional

class ChessRobotController:
    """
    Contrôleur pour un robot d'échecs utilisant G-code via port série.
    Lit les coups depuis bestmove.txt et convertit en mouvements physiques.
    """
    
    def __init__(self, port: str = 'COM3', baudrate: int = 115200, config_file: str = 'robot_config.ini'):
        """
        Initialise le contrôleur du robot.

        Args:
            port: Port série (ex: 'COM3' sous Windows, '/dev/ttyUSB0' sous Linux)
            baudrate: Vitesse de communication (115200 par défaut)
            config_file: Chemin vers le fichier de configuration
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.stop_monitoring = Event()

        # Charger la configuration depuis robot_config.ini
        self.load_config(config_file)

        self.capture_count = 0

    def load_config(self, config_file: str):
        """Charge la configuration depuis robot_config.ini"""
        config = configparser.ConfigParser()

        if os.path.exists(config_file):
            config.read(config_file)
            print(f"[CONFIG] Configuration chargée depuis {config_file}")
        else:
            print(f"[AVERTISSEMENT] {config_file} non trouvé - utilisation des valeurs par défaut")
            # Valeurs par défaut
            config['BOARD'] = {
                'square_size': '50.0',
                'board_offset_x': '20.0',
                'board_offset_y': '20.0'
            }
            config['HEIGHTS'] = {
                'z_safe': '50.0',
                'z_grab': '5.0',
                'z_lift': '30.0'
            }
            config['CAPTURE_ZONE'] = {
                'capture_x': '450.0',
                'capture_y': '50.0',
                'capture_spacing': '30.0'
            }
            config['SPEEDS'] = {
                'feed_rate_travel': '3000',
                'feed_rate_work': '1500'
            }
            config['GRIPPER'] = {
                'grab_command': 'M3 S1000',
                'release_command': 'M5',
                'grab_delay': '0.5',
                'release_delay': '0.5'
            }

        # Charger les paramètres du plateau
        self.SQUARE_SIZE = float(config['BOARD']['square_size'])
        self.BOARD_OFFSET_X = float(config['BOARD']['board_offset_x'])
        self.BOARD_OFFSET_Y = float(config['BOARD']['board_offset_y'])

        # Charger les hauteurs Z
        self.Z_SAFE = float(config['HEIGHTS']['z_safe'])
        self.Z_GRAB = float(config['HEIGHTS']['z_grab'])
        self.Z_LIFT = float(config['HEIGHTS']['z_lift'])

        # Zone de capture
        self.CAPTURE_ZONE_X = float(config['CAPTURE_ZONE']['capture_x'])
        self.CAPTURE_ZONE_Y = float(config['CAPTURE_ZONE']['capture_y'])
        self.CAPTURE_SPACING = float(config['CAPTURE_ZONE']['capture_spacing'])

        # Vitesses
        self.FEED_RATE_TRAVEL = int(config['SPEEDS']['feed_rate_travel'])
        self.FEED_RATE_WORK = int(config['SPEEDS']['feed_rate_work'])

        # Préhension
        self.GRAB_COMMAND = config['GRIPPER']['grab_command']
        self.RELEASE_COMMAND = config['GRIPPER']['release_command']
        self.GRAB_DELAY = float(config['GRIPPER']['grab_delay'])
        self.RELEASE_DELAY = float(config['GRIPPER']['release_delay'])

        # Axe Z (servo)
        if 'Z_AXIS' in config:
            self.Z_UP_COMMAND = config['Z_AXIS'].get('z_up_command', 'M280 P0 S12')
            self.Z_DOWN_COMMAND = config['Z_AXIS'].get('z_down_command', 'M280 P0 S168')
            self.Z_MOVE_DELAY = float(config['Z_AXIS'].get('z_move_delay', '0.5'))
        else:
            # Valeurs par défaut
            self.Z_UP_COMMAND = 'M280 P0 S12'
            self.Z_DOWN_COMMAND = 'M280 P0 S168'
            self.Z_MOVE_DELAY = 0.5

        # Paramètres avancés
        if 'ADVANCED' in config:
            self.XY_SETTLE_DELAY = float(config['ADVANCED'].get('xy_settle_delay', '1.0'))
        else:
            self.XY_SETTLE_DELAY = 1.0

        print(f"[CONFIG] Plateau: {self.SQUARE_SIZE}mm/case, offset=({self.BOARD_OFFSET_X}, {self.BOARD_OFFSET_Y})")
        print(f"[CONFIG] Hauteurs: safe={self.Z_SAFE}, grab={self.Z_GRAB}, lift={self.Z_LIFT}")
        print(f"[CONFIG] Axe Z: UP={self.Z_UP_COMMAND}, DOWN={self.Z_DOWN_COMMAND}")
        print(f"[CONFIG] Délai stabilisation XY: {self.XY_SETTLE_DELAY}s")

    def connect(self) -> bool:
        """
        Établit la connexion avec le robot via port série.
        
        Returns:
            True si la connexion est établie, False sinon
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2,
                write_timeout=2
            )
            time.sleep(2)  # Attendre la réinitialisation de l'Arduino/GRBL
            
            # Attendre le message de démarrage
            startup_msg = self.serial_conn.read_until(b'\n')
            print(f"[ROBOT] Démarrage: {startup_msg.decode(errors='ignore').strip()}")
            
            # Initialiser le robot
            self.send_command("G21")  # Mode millimètres
            self.send_command("G90")  # Positionnement absolu
            self.send_command("G94")  # Vitesse en mm/min
            self.send_command(f"F{self.FEED_RATE_TRAVEL}")  # Vitesse par défaut
            
            self.is_connected = True
            print(f"[ROBOT] Connecté sur {self.port} à {self.baudrate} bauds")
            return True
            
        except serial.SerialException as e:
            print(f"[ERREUR] Impossible de se connecter: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Ferme la connexion série."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("[ROBOT] Déconnecté")
    
    def send_command(self, command: str, wait_ok: bool = True) -> bool:
        """
        Envoie une commande G-code au robot.
        
        Args:
            command: Commande G-code à envoyer
            wait_ok: Attendre la réponse 'ok' du robot
            
        Returns:
            True si la commande est acceptée, False sinon
        """
        if not self.is_connected or not self.serial_conn:
            print("[ERREUR] Robot non connecté")
            return False
        
        try:
            # Envoyer la commande
            cmd_line = command.strip() + '\n'
            self.serial_conn.write(cmd_line.encode())
            print(f"[ROBOT] >>> {command}")
            
            if wait_ok:
                # Attendre la réponse
                while True:
                    response = self.serial_conn.readline().decode(errors='ignore').strip()
                    if response:
                        print(f"[ROBOT] <<< {response}")
                        if 'ok' in response.lower():
                            return True
                        elif 'error' in response.lower():
                            print(f"[ERREUR] Commande rejetée: {command}")
                            return False
            
            return True
            
        except Exception as e:
            print(f"[ERREUR] Envoi commande: {e}")
            return False
    
    def home_robot(self):
        """
        Initialise la position du robot :
        1. Exécute le cycle de homing G28 pour trouver le point zéro physique.
        2. Se déplace au-dessus du coin a1 du plateau pour être prêt à jouer.
        """
        print("[ROBOT] Initialisation de la position...")

        # Étape 1: Homing physique pour trouver l'origine (0,0,0)
        # Le robot va toucher ses capteurs de fin de course.
        print("[ROBOT] Étape 1/2 - Lancement du Homing (G28 X Y) si vous voulez faire le homming du Z, changez ligne ""self.send_command(""G28 X Y"")")
        self.send_command("G28 X Y")
        #time.sleep(1) # Petite pause pour s'assurer que G28 est terminé

        # Étape 2: Se positionner au-dessus du coin a1 comme position de départ
        # On s'assure d'abord que l'axe Z est à une hauteur de sécurité.
        print(f"[ROBOT] Étape 2/2 - Déplacement vers la position de départ (coin a1)...")
        
        # Commande 1 : Monter l'axe Z à la hauteur de sécurité
        self.send_command(f"G0 Z{self.Z_SAFE}")

        # Commande 2 : Aller aux coordonnées X/Y du coin a1
        # Ces coordonnées (self.BOARD_OFFSET_X/Y) viennent de votre calibration !
        self.send_command(f"G0 X{self.BOARD_OFFSET_X} Y{self.BOARD_OFFSET_Y}")
        
        print("[ROBOT] Initialisation terminée. Robot en position d'attente au-dessus de a1.")
    
    def uci_to_coordinates(self, uci_square: str) -> Tuple[float, float]:
        """
        Convertit une case UCI (ex: 'e4') en coordonnées X,Y en mm.

        Convention des axes:
        - Axe X va de a1 à a8 (rang 1-8, vertical sur le plateau)
        - Axe Y va de a1 à h1 (colonne a-h, horizontal sur le plateau)

        Args:
            uci_square: Case au format UCI (a1-h8)

        Returns:
            Tuple (x, y) en millimètres
        """
        file = ord(uci_square[0]) - ord('a')  # 0-7 (a-h)
        rank = int(uci_square[1]) - 1         # 0-7 (1-8)

        # Convention: X = rang (1-8), Y = colonne (a-h)
        x = self.BOARD_OFFSET_X + (rank * self.SQUARE_SIZE) + (self.SQUARE_SIZE / 2)
        y = self.BOARD_OFFSET_Y + (file * self.SQUARE_SIZE) + (self.SQUARE_SIZE / 2)

        return (x, y)
    
    def move_z(self, z_target: float):
        """
        Déplace l'axe Z en utilisant les commandes servo M280.

        Args:
            z_target: Hauteur cible (compare avec Z_GRAB pour déterminer UP/DOWN)
        """
        # Si z_target est proche de Z_GRAB, descendre, sinon monter
        if z_target <= self.Z_GRAB:
            print(f"[Z-AXIS] Descente (Z={z_target:.2f}mm)")
            self.send_command(self.Z_DOWN_COMMAND)
        else:
            print(f"[Z-AXIS] Montée (Z={z_target:.2f}mm)")
            self.send_command(self.Z_UP_COMMAND)
        time.sleep(self.Z_MOVE_DELAY)

    def move_to_position(self, x: float, y: float, z: float, feed_rate: int = None):
        """
        Déplace le robot à une position donnée.
        Utilise G0 pour X et Y, et M280 pour Z.
        Attend la stabilisation XY avant de bouger Z.

        Args:
            x, y, z: Coordonnées en millimètres
            feed_rate: Vitesse de déplacement pour X et Y (optionnelle)
        """
        # Déplacer X et Y avec G0
        if feed_rate:
            self.send_command(f"G0 X{x:.2f} Y{y:.2f} F{feed_rate}")
        else:
            self.send_command(f"G0 X{x:.2f} Y{y:.2f}")

        # IMPORTANT: Attendre que les axes XY atteignent leur position
        # avant de bouger l'axe Z (évite que la pince descende en vol)
        print(f"[WAIT] Attente stabilisation XY ({self.XY_SETTLE_DELAY}s)...")
        time.sleep(self.XY_SETTLE_DELAY)

        # Déplacer Z avec M280
        self.move_z(z)
    
    def grab_piece(self):
        """
        Active le mécanisme de préhension (électro-aimant ou pince).
        Utilise la commande configurée dans robot_config.ini
        """
        self.send_command(self.GRAB_COMMAND)
        time.sleep(self.GRAB_DELAY)

    def release_piece(self):
        """Désactive le mécanisme de préhension."""
        self.send_command(self.RELEASE_COMMAND)
        time.sleep(self.RELEASE_DELAY)
    
    def execute_move(self, uci_move: str, is_capture: bool = False):
        """
        Exécute un mouvement d'échecs sur le robot.
        
        Args:
            uci_move: Coup au format UCI (ex: 'e2e4', 'g1f3')
            is_capture: True si c'est une capture
        """
        if len(uci_move) < 4:
            print(f"[ERREUR] Format UCI invalide: {uci_move}")
            return
        
        from_square = uci_move[:2]
        to_square = uci_move[2:4]
        
        print(f"\n[ROBOT] Exécution du coup: {from_square} → {to_square}")
        
        # Convertir en coordonnées physiques
        from_x, from_y = self.uci_to_coordinates(from_square)
        to_x, to_y = self.uci_to_coordinates(to_square)
        
        # Si c'est une capture, déplacer d'abord la pièce capturée
        if is_capture:
            print("[ROBOT] Capture détectée - déplacement de la pièce adverse")
            self.remove_captured_piece(to_x, to_y)
        
        # 1. Aller au-dessus de la pièce source
        print(f"[ROBOT] Position de départ: {from_square}")
        self.move_to_position(from_x, from_y, self.Z_SAFE, self.FEED_RATE_TRAVEL)
        
        # 2. Descendre pour attraper
        self.move_to_position(from_x, from_y, self.Z_GRAB, self.FEED_RATE_WORK)
        
        # 3. Activer la préhension
        self.grab_piece()
        
        # 4. Remonter avec la pièce
        self.move_to_position(from_x, from_y, self.Z_LIFT, self.FEED_RATE_WORK)
        
        # 5. Se déplacer vers la destination
        print(f"[ROBOT] Position d'arrivée: {to_square}")
        self.move_to_position(to_x, to_y, self.Z_LIFT, self.FEED_RATE_TRAVEL)
        
        # 6. Descendre pour déposer
        self.move_to_position(to_x, to_y, self.Z_GRAB, self.FEED_RATE_WORK)
        
        # 7. Relâcher la pièce
        self.release_piece()
        
        # 8. Remonter
        self.move_to_position(to_x, to_y, self.Z_SAFE, self.FEED_RATE_WORK)
        
        print(f"[ROBOT] Coup {uci_move} terminé ✓")
    
    def remove_captured_piece(self, x: float, y: float):
        """
        Retire une pièce capturée et la place dans la zone de capture.

        Args:
            x, y: Coordonnées de la pièce à capturer
        """
        # Position dans la zone de capture
        capture_x = self.CAPTURE_ZONE_X + (self.capture_count % 8) * self.CAPTURE_SPACING
        capture_y = self.CAPTURE_ZONE_Y + (self.capture_count // 8) * self.CAPTURE_SPACING
        self.capture_count += 1
        
        # Aller chercher la pièce
        self.move_to_position(x, y, self.Z_SAFE, self.FEED_RATE_TRAVEL)
        self.move_to_position(x, y, self.Z_GRAB, self.FEED_RATE_WORK)
        self.grab_piece()
        self.move_to_position(x, y, self.Z_LIFT, self.FEED_RATE_WORK)
        
        # Déplacer vers la zone de capture
        self.move_to_position(capture_x, capture_y, self.Z_LIFT, self.FEED_RATE_TRAVEL)
        self.move_to_position(capture_x, capture_y, self.Z_GRAB, self.FEED_RATE_WORK)
        self.release_piece()
        self.move_to_position(capture_x, capture_y, self.Z_SAFE, self.FEED_RATE_WORK)

    def parse_next_move(self, move_line: str) -> dict:
        """
        Parse le format du fichier next_move.txt: {couleur};{mouvement}

        Args:
            move_line: Ligne du fichier (ex: "B;e2e4" ou "N;g8f6")

        Returns:
            Dictionnaire avec 'color' et 'move', ou None si invalide

        Examples:
            "B;e2e4" -> {'color': 'B', 'move': 'e2e4', 'is_white': True}
            "N;g8f6" -> {'color': 'N', 'move': 'g8f6', 'is_white': False}
        """
        try:
            parts = move_line.strip().split(';')
            if len(parts) != 2:
                print(f"[ERREUR] Format invalide: {move_line} (doit être 'couleur;mouvement')")
                return None

            color = parts[0].strip().upper()
            move = parts[1].strip().lower()

            # Vérifier la couleur
            if color not in ['B', 'N', 'W']:  # B=Blanc, N=Noir, W=White
                print(f"[ERREUR] Couleur invalide: {color} (doit être B ou N)")
                return None

            # Vérifier le format du mouvement (au moins 4 caractères: e2e4)
            if len(move) < 4:
                print(f"[ERREUR] Mouvement invalide: {move}")
                return None

            return {
                'color': color,
                'move': move,
                'is_white': color in ['B', 'W']
            }

        except Exception as e:
            print(f"[ERREUR] Erreur lors du parsing: {e}")
            return None

    def monitor_next_move_file(self, filename: str = "next_move.txt", callback=None):
        """
        Surveille le fichier next_move.txt et exécute les coups automatiquement.
        Format attendu: {couleur};{mouvement}
        Exemple: B;e2e4 (Blanc joue e2 vers e4)

        Args:
            filename: Nom du fichier à surveiller
            callback: Fonction appelée après chaque mouvement
        """
        last_move = ""
        last_modified = 0

        # Si un chemin relatif est fourni, le construire depuis le dossier parent
        if not os.path.isabs(filename):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            filename = os.path.join(parent_dir, filename)

        print(f"[ROBOT] Surveillance du fichier {filename}...")
        print("[INFO] Format attendu: couleur;mouvement (ex: B;e2e4)")

        while not self.stop_monitoring.is_set():
            try:
                if os.path.exists(filename):
                    current_modified = os.path.getmtime(filename)

                    # Si le fichier a été modifié
                    if current_modified != last_modified:
                        last_modified = current_modified

                        with open(filename, 'r') as f:
                            move_line = f.read().strip()

                        # Si c'est un nouveau coup
                        if move_line and move_line != last_move:
                            last_move = move_line
                            print(f"\n[ROBOT] Nouvelle instruction détectée: {move_line}")

                            # Parser le coup
                            parsed = self.parse_next_move(move_line)
                            if parsed:
                                color_name = "Blanc" if parsed['is_white'] else "Noir"
                                print(f"[ROBOT] Couleur: {color_name}, Coup: {parsed['move']}")

                                # Exécuter le mouvement
                                # TODO: Intégrer la détection de capture avec votre logique de jeu
                                self.execute_move(parsed['move'], is_capture=False)

                                if callback:
                                    callback(parsed)

                time.sleep(0.5)  # Vérifier toutes les 500ms

            except Exception as e:
                print(f"[ERREUR] Surveillance: {e}")
                time.sleep(1)

    def monitor_bestmove_file(self, filename: str = "bestmove.txt", callback=None):
        """
        Surveille le fichier bestmove.txt et exécute les coups automatiquement.

        Args:
            filename: Nom du fichier à surveiller (peut être un chemin relatif ou absolu)
            callback: Fonction appelée après chaque mouvement
        """
        last_move = ""
        last_modified = 0

        # Si un chemin relatif est fourni, le construire depuis le dossier parent
        if not os.path.isabs(filename):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            filename = os.path.join(parent_dir, filename)

        print(f"[ROBOT] Surveillance du fichier {filename}...")

        while not self.stop_monitoring.is_set():
            try:
                if os.path.exists(filename):
                    current_modified = os.path.getmtime(filename)
                    
                    # Si le fichier a été modifié
                    if current_modified != last_modified:
                        last_modified = current_modified
                        
                        with open(filename, 'r') as f:
                            move = f.read().strip()
                        
                        # Si c'est un nouveau coup
                        if move and move != last_move and len(move) >= 4:
                            last_move = move
                            print(f"\n[ROBOT] Nouveau coup détecté: {move}")
                            
                            # Exécuter le mouvement
                            # TODO: Déterminer si c'est une capture
                            # Vous devrez intégrer cela avec votre logique de jeu
                            self.execute_move(move, is_capture=False)
                            
                            if callback:
                                callback(move)
                
                time.sleep(0.5)  # Vérifier toutes les 500ms
                
            except Exception as e:
                print(f"[ERREUR] Surveillance: {e}")
                time.sleep(1)
    
    def start_monitoring(self, filename: str = "bestmove.txt", callback=None):
        """Démarre la surveillance de bestmove.txt dans un thread séparé."""
        self.stop_monitoring.clear()
        monitor_thread = Thread(target=self.monitor_bestmove_file,
                               args=(filename, callback))
        monitor_thread.daemon = True
        monitor_thread.start()
        return monitor_thread

    def start_monitoring_next_move(self, filename: str = "next_move.txt", callback=None):
        """
        Démarre la surveillance de next_move.txt dans un thread séparé.

        Args:
            filename: Nom du fichier à surveiller (défaut: next_move.txt)
            callback: Fonction appelée après chaque mouvement

        Returns:
            Le thread de surveillance
        """
        self.stop_monitoring.clear()
        monitor_thread = Thread(target=self.monitor_next_move_file,
                               args=(filename, callback))
        monitor_thread.daemon = True
        monitor_thread.start()
        print(f"[ROBOT] Surveillance de {filename} démarrée")
        return monitor_thread

    def stop(self):
        """Arrête la surveillance et retourne à la position d'origine."""
        self.stop_monitoring.set()
        self.home_robot()
        self.disconnect()


# ==================== EXEMPLE D'UTILISATION ====================

def main():
    """Exemple d'utilisation du contrôleur."""
    
    # Configuration - ADAPTER À VOTRE ROBOT
    SERIAL_PORT = 'COM3'  # Windows: 'COM3', Linux: '/dev/ttyUSB0'
    BAUDRATE = 250000
    
    print("="*60)
    print("CONTRÔLEUR ROBOT D'ÉCHECS - G-CODE")
    print("="*60)
    
    # Créer le contrôleur
    robot = ChessRobotController(port=SERIAL_PORT, baudrate=BAUDRATE)
    
    # 1. Tenter de se connecter
    if robot.connect():
        # 2. Si la connexion est réussie, lancer l'initialisation
        robot.home_robot()
    
        print("\nOptions:")
        print("1. Mode surveillance automatique (bestmove.txt)")
        print("2. Mode surveillance next_move.txt (format: couleur;mouvement)")
        print("3. Mode test manuel")
        print("4. Quitter")

        choice = input("\nVotre choix: ")

        if choice == '1':
            # Mode automatique - surveille bestmove.txt
            def on_move_complete(move):
                print(f"[INFO] Mouvement {move} terminé - prêt pour le suivant")

            print("\n[INFO] Démarrage de la surveillance automatique...")
            print("[INFO] Jouez contre Stockfish et le robot exécutera ses coups")
            print("[INFO] Appuyez sur Ctrl+C pour arrêter\n")

            robot.start_monitoring(callback=on_move_complete)

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[INFO] Arrêt demandé par l'utilisateur")

        elif choice == '2':
            # Mode surveillance next_move.txt
            def on_next_move_complete(parsed_move):
                color_name = "Blanc" if parsed_move['is_white'] else "Noir"
                print(f"[INFO] {color_name} - {parsed_move['move']} terminé - prêt pour le suivant")

            print("\n[INFO] Démarrage de la surveillance de next_move.txt...")
            print("[INFO] Format: couleur;mouvement (ex: B;e2e4)")
            print("[INFO] Appuyez sur Ctrl+C pour arrêter\n")

            robot.start_monitoring_next_move(callback=on_next_move_complete)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[INFO] Arrêt demandé par l'utilisateur")

        elif choice == '3':
            # Mode test manuel
            print("\n[INFO] Mode test - Entrez des coups UCI (ex: e2e4)")
            print("[INFO] Tapez 'quit' pour quitter\n")

            while True:
                move = input("Coup UCI (ou 'quit'): ").strip().lower()

                if move == 'quit':
                    break

                if len(move) >= 4:
                    is_capture = input("Capture? (o/n): ").lower() == 'o'
                    robot.execute_move(move, is_capture)
                else:
                    print("Format invalide. Exemple: e2e4")
    else:
        # Si la connexion a échoué, afficher une erreur et arrêter
        print("\n[ERREUR FATALE] Impossible de continuer sans connexion au robot.")
        print("Vérifiez le port, le baudrate et le câble.")

    # Nettoyage
    robot.stop()
    print("\n[INFO] Programme terminé")


if __name__ == "__main__":
    main()
