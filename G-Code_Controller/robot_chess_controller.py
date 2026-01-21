import serial
import time
import os
import configparser
from threading import Thread, Event
from typing import Tuple, Optional
from threading import Thread, Event

class ChessRobotController:
    """
    Contrôleur pour un robot d'échecs utilisant G-code via port série.
    Lit les coups depuis bestmove.txt et convertit en mouvements physiques.
    """
    
    def __init__(self, port: str = 'COM5', baudrate: int = 250000, config_file: str = 'robot_config.ini'):
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

        # Construire le chemin absolu du fichier de config s'il est relatif
        if not os.path.isabs(config_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(script_dir, config_file)

        # Charger la configuration depuis robot_config.ini
        self.load_config(config_file)

        self.capture_count = 0
        self.white_capture_count = 0  # Pièces blanches capturées
        self.black_capture_count = 0  # Pièces noires capturées

        # Tracking de l'état du plateau pour connaître la couleur des pièces
        self.board_state = {}
        self.captured_pieces = []  # List to store captured pieces: {'type', 'color', 'storage_pos'}
        self.init_board_state()

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

        # Charger les paramètres série (écrase les valeurs passées au constructeur)
        if 'SERIAL' in config:
            self.port = config['SERIAL'].get('port', self.port)
            self.baudrate = int(config['SERIAL'].get('baudrate', self.baudrate))
            print(f"[CONFIG] Port série: {self.port} à {self.baudrate} bauds")

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

        # Pronation (servo de rotation de la pince)
        if 'PRONATION' in config:
            self.PRONATION_ENABLED = config['PRONATION'].get('pronation_enabled', 'false').lower() == 'true'
            self.PRONATION_PIN = int(config['PRONATION'].get('pronation_pin', '0'))
            self.PRONATION_NEUTRAL = int(config['PRONATION'].get('pronation_neutral', '90'))
            self.PRONATION_LEFT = int(config['PRONATION'].get('pronation_left', '0'))
            self.PRONATION_RIGHT = int(config['PRONATION'].get('pronation_right', '180'))
            self.PRONATION_DELAY = float(config['PRONATION'].get('pronation_delay', '0.3'))
        else:
            self.PRONATION_ENABLED = False
            self.PRONATION_PIN = 0
            self.PRONATION_NEUTRAL = 90
            self.PRONATION_LEFT = 0
            self.PRONATION_RIGHT = 180
            self.PRONATION_DELAY = 0.3

        print(f"[CONFIG] Plateau: {self.SQUARE_SIZE}mm/case, offset=({self.BOARD_OFFSET_X}, {self.BOARD_OFFSET_Y})")
        print(f"[CONFIG] Hauteurs: safe={self.Z_SAFE}, grab={self.Z_GRAB}, lift={self.Z_LIFT}")
        print(f"[CONFIG] Axe Z: UP={self.Z_UP_COMMAND}, DOWN={self.Z_DOWN_COMMAND}")
        print(f"[CONFIG] Délai stabilisation XY: {self.XY_SETTLE_DELAY}s")
        if self.PRONATION_ENABLED:
            print(f"[CONFIG] Pronation: P{self.PRONATION_PIN}, neutre={self.PRONATION_NEUTRAL}°, gauche={self.PRONATION_LEFT}°, droite={self.PRONATION_RIGHT}°")

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
    
    def init_board_state(self):
        """Initialise l'état du plateau avec la position de départ des échecs."""
        self.board_state = {}
        
        # Pièces blanches (rang 1 et 2)
        for file in 'abcdefgh':
            self.board_state[f"{file}2"] = {"color": "white", "type": "pawn"}
            
        self.board_state.update({
            "a1": {"color": "white", "type": "rook"}, "h1": {"color": "white", "type": "rook"},
            "b1": {"color": "white", "type": "knight"}, "g1": {"color": "white", "type": "knight"},
            "c1": {"color": "white", "type": "bishop"}, "f1": {"color": "white", "type": "bishop"},
            "d1": {"color": "white", "type": "queen"}, "e1": {"color": "white", "type": "king"}
        })

        # Pièces noires (rang 7 et 8)
        for file in 'abcdefgh':
            self.board_state[f"{file}7"] = {"color": "black", "type": "pawn"}
            
        self.board_state.update({
            "a8": {"color": "black", "type": "rook"}, "h8": {"color": "black", "type": "rook"},
            "b8": {"color": "black", "type": "knight"}, "g8": {"color": "black", "type": "knight"},
            "c8": {"color": "black", "type": "bishop"}, "f8": {"color": "black", "type": "bishop"},
            "d8": {"color": "black", "type": "queen"}, "e8": {"color": "black", "type": "king"}
        })

    def update_board_state(self, move_uci: str):
        """
        Met à jour l'état du plateau après un coup.

        Args:
            move_uci: Coup UCI (ex: 'e2e4')
        """
        from_square = move_uci[:2]
        to_square = move_uci[2:4]

        # Déplacer la pièce
        if from_square in self.board_state:
            piece_data = self.board_state[from_square]
            self.board_state[to_square] = piece_data
            del self.board_state[from_square]

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
        Déplace l'axe Z en utilisant G0 (stepper) ou les commandes configurées.

        Args:
            z_target: Hauteur cible en mm
        """
        # Vérifier si les commandes Z sont des G0 (stepper) ou M280 (servo)
        if self.Z_UP_COMMAND.startswith('G0') or self.Z_UP_COMMAND.startswith('G1'):
            # Mode stepper : utiliser G0 Z directement avec la hauteur cible
            print(f"[Z-AXIS] Déplacement vers Z={z_target:.2f}mm")
            self.send_command(f"G0 Z{z_target:.2f} F{self.FEED_RATE_TRAVEL}")
        else:
            # Mode servo : utiliser les commandes UP/DOWN configurées
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

    # ==================== FONCTIONS DE PRONATION ====================

    def pronation_set_angle(self, angle: int):
        """
        Définit l'angle du servo de pronation.

        Args:
            angle: Angle en degrés (0-180)
        """
        if not self.PRONATION_ENABLED:
            print("[PRONATION] Pronation désactivée dans la config")
            return

        angle = max(0, min(180, angle))  # Limiter entre 0 et 180
        cmd = f"M280 P{self.PRONATION_PIN} S{angle}"
        print(f"[PRONATION] Rotation vers {angle}°")
        self.send_command(cmd)
        time.sleep(self.PRONATION_DELAY)

    def pronation_neutral(self):
        """Place la pince en position neutre."""
        self.pronation_set_angle(self.PRONATION_NEUTRAL)

    def pronation_left(self):
        """Tourne la pince vers la gauche."""
        self.pronation_set_angle(self.PRONATION_LEFT)

    def pronation_right(self):
        """Tourne la pince vers la droite."""
        self.pronation_set_angle(self.PRONATION_RIGHT)

    def execute_castling(self, king_from: str, king_to: str, rook_from: str, rook_to: str):
        """
        Exécute un roque (roi + tour).

        Args:
            king_from: Case de départ du roi (ex: 'e1')
            king_to: Case d'arrivée du roi (ex: 'g1')
            rook_from: Case de départ de la tour (ex: 'h1')
            rook_to: Case d'arrivée de la tour (ex: 'f1')
        """
        print(f"[ROBOT] === EXÉCUTION DU ROQUE ===")

        # 1. Déplacer le roi
        print(f"[ROBOT] Étape 1/2 : Déplacement du roi {king_from} → {king_to}")
        king_from_x, king_from_y = self.uci_to_coordinates(king_from)
        king_to_x, king_to_y = self.uci_to_coordinates(king_to)

        self.move_to_position(king_from_x, king_from_y, self.Z_SAFE, self.FEED_RATE_TRAVEL)
        self.move_to_position(king_from_x, king_from_y, self.Z_GRAB, self.FEED_RATE_WORK)
        self.grab_piece()
        self.move_to_position(king_from_x, king_from_y, self.Z_LIFT, self.FEED_RATE_WORK)
        self.move_to_position(king_to_x, king_to_y, self.Z_LIFT, self.FEED_RATE_TRAVEL)
        self.move_to_position(king_to_x, king_to_y, self.Z_GRAB, self.FEED_RATE_WORK)
        self.release_piece()
        self.move_to_position(king_to_x, king_to_y, self.Z_SAFE, self.FEED_RATE_WORK)

        # 2. Déplacer la tour
        print(f"[ROBOT] Étape 2/2 : Déplacement de la tour {rook_from} → {rook_to}")
        rook_from_x, rook_from_y = self.uci_to_coordinates(rook_from)
        rook_to_x, rook_to_y = self.uci_to_coordinates(rook_to)

        self.move_to_position(rook_from_x, rook_from_y, self.Z_SAFE, self.FEED_RATE_TRAVEL)
        self.move_to_position(rook_from_x, rook_from_y, self.Z_GRAB, self.FEED_RATE_WORK)
        self.grab_piece()
        self.move_to_position(rook_from_x, rook_from_y, self.Z_LIFT, self.FEED_RATE_WORK)
        self.move_to_position(rook_to_x, rook_to_y, self.Z_LIFT, self.FEED_RATE_TRAVEL)
        self.move_to_position(rook_to_x, rook_to_y, self.Z_GRAB, self.FEED_RATE_WORK)
        self.release_piece()
        self.move_to_position(rook_to_x, rook_to_y, self.Z_SAFE, self.FEED_RATE_WORK)

        # 3. Mettre à jour le board_state
        king_data = self.board_state.get(king_from)
        self.board_state[king_to] = king_data
        
        rook_data = self.board_state.get(rook_from)
        self.board_state[rook_to] = rook_data
        
        del self.board_state[king_from]
        del self.board_state[rook_from]

        print(f"[ROBOT] Roque terminé ✓")

    def is_castling(self, uci_move: str) -> tuple:
        """
        Détermine si un coup est un roque et retourne les infos nécessaires.

        Args:
            uci_move: Coup UCI (ex: 'e1g1' pour petit roque blanc)

        Returns:
            (is_castling, rook_from, rook_to) ou (False, None, None)
        """
        from_square = uci_move[:2]
        to_square = uci_move[2:4]

        # Petit roque blanc (e1g1)
        if from_square == 'e1' and to_square == 'g1':
            return (True, 'h1', 'f1')
        # Grand roque blanc (e1c1)
        elif from_square == 'e1' and to_square == 'c1':
            return (True, 'a1', 'd1')
        # Petit roque noir (e8g8)
        elif from_square == 'e8' and to_square == 'g8':
            return (True, 'h8', 'f8')
        # Grand roque noir (e8c8)
        elif from_square == 'e8' and to_square == 'c8':
            return (True, 'a8', 'd8')

        return (False, None, None)

    def is_en_passant(self, uci_move: str) -> str:
        """
        Détermine si un coup est une prise en passant.

        Args:
            uci_move: Coup UCI (ex: 'e5d6')

        Returns:
            Case du pion capturé (ex: 'd5') ou None
        """
        from_square = uci_move[:2]
        to_square = uci_move[2:4]

        # Vérifier si c'est un pion
        piece_data = self.board_state.get(from_square)
        if piece_data is None:
            return None

        # Prise en passant : mouvement diagonal d'un pion vers une case vide
        from_file, from_rank = from_square[0], int(from_square[1])
        to_file, to_rank = to_square[0], int(to_square[1])

        # Mouvement diagonal
        if from_file != to_file:
            # Case de destination vide dans board_state
            if to_square not in self.board_state:
                # C'est probablement une prise en passant
                # Le pion capturé est sur le même rang que la case de départ
                captured_pawn_square = f"{to_file}{from_rank}"
                if captured_pawn_square in self.board_state:
                    return captured_pawn_square

        return None

    # Dans le fichier robot_chess_controller.py

    def execute_move(self, uci_move: str, is_capture: bool = False):
        """
        Exécute un mouvement d'échecs sur le robot, en gérant les captures,
        le roque et la prise en passant.

        Args:
            uci_move: Coup au format UCI (ex: 'e2e4', 'g1f3')
            is_capture: True si le coup est une capture (fourni par le moteur de jeu)
        """
        # --- 1. Validation de base ---
        if len(uci_move) < 4:
            print(f"[ROBOT] [ERREUR] Format UCI invalide reçu: '{uci_move}'. Annulation du coup.")
            return

        from_square = uci_move[:2]
        to_square = uci_move[2:4]
        print(f"\n[ROBOT] [INFO] Reçu nouvelle instruction: {from_square} → {to_square} (Capture: {is_capture})")

        # --- 2. Gestion des coups spéciaux (Roque) ---
        is_castling_move, rook_from, rook_to = self.is_castling(uci_move)
        if is_castling_move:
            print(f"[ROBOT] [INFO] Coup spécial détecté: ROQUE.")
            self.execute_castling(from_square, to_square, rook_from, rook_to)
            print(f"[ROBOT] [SUCCESS] Roque {uci_move} terminé.")
            return

        # --- 3. Gestion de la capture (si nécessaire) ---
        captured_piece_square = None  # Retiendra la case de la pièce capturée

        # Cas spécial : Prise en Passant
        en_passant_square = self.is_en_passant(uci_move)
        if en_passant_square:
            print(f"[ROBOT] [INFO] Coup spécial détecté: PRISE EN PASSANT. Pion capturé en {en_passant_square}.")
            captured_piece_square = en_passant_square
        # Cas d'une capture normale
        elif is_capture:
            print("[ROBOT] [INFO] Capture normale détectée.")
            captured_piece_square = to_square

        # S'il y a bien une pièce à capturer, on la retire du plateau en premier
        if captured_piece_square:
            captured_piece_data = self.board_state.get(captured_piece_square)
            
            # Sécurité : vérifier que le robot pense bien qu'il y a une pièce à cet endroit
            if captured_piece_data is None:
                print(f"[ROBOT] [ERREUR] Désynchronisation! Le jeu a signalé une capture en {captured_piece_square}, mais le robot ne voit aucune pièce à cet endroit.")
            else:
                print(f"[ROBOT] [ACTION] Début de la procédure de capture pour la pièce {captured_piece_data} en {captured_piece_square}.")
                is_white_captured = (captured_piece_data['color'] == "white")
                cap_x, cap_y = self.uci_to_coordinates(captured_piece_square)
                
                # Séquence de retrait de la pièce capturée
                self.remove_captured_piece(cap_x, cap_y, is_white_piece=is_white_captured, captured_piece_data=captured_piece_data)
                
                # Mettre à jour l'état du plateau IMMÉDIATEMENT pour la pièce capturée
                del self.board_state[captured_piece_square]
                print(f"[ROBOT] [STATE] Pièce en {captured_piece_square} retirée de l'état interne.")

        # --- 4. Exécution du mouvement principal de la pièce ---
        from_x, from_y = self.uci_to_coordinates(from_square)
        to_x, to_y = self.uci_to_coordinates(to_square)

        print(f"[ROBOT] [ACTION] Déplacement de la pièce de {from_square} à {to_square}.")

        # Séquence "Pick and Place"
        # 1. Aller au-dessus de la pièce source
        self.move_to_position(from_x, from_y, self.Z_SAFE, self.FEED_RATE_TRAVEL)
        # 2. Descendre pour attraper
        self.move_to_position(from_x, from_y, self.Z_GRAB, self.FEED_RATE_WORK)
        # 3. Activer la préhension
        self.grab_piece()
        # 4. Remonter avec la pièce
        self.move_to_position(from_x, from_y, self.Z_LIFT, self.FEED_RATE_WORK)
        # 5. Se déplacer vers la destination
        self.move_to_position(to_x, to_y, self.Z_LIFT, self.FEED_RATE_TRAVEL)
        # 6. Descendre pour déposer
        self.move_to_position(to_x, to_y, self.Z_GRAB, self.FEED_RATE_WORK)
        # 7. Relâcher la pièce
        self.release_piece()
        # 8. Remonter à une hauteur de sécurité
        self.move_to_position(to_x, to_y, self.Z_SAFE, self.FEED_RATE_WORK)

        # --- 5. Mise à jour de l'état interne du plateau pour la pièce déplacée ---
        self.update_board_state(uci_move)
        print(f"[ROBOT] [STATE] État interne mis à jour pour le coup {uci_move}.")
        print(f"[ROBOT] [SUCCESS] Coup {uci_move} terminé ✓")
        
    def get_capture_zone_position(self, is_white_piece: bool):
        """
        Calcule la position de la zone de capture pour une pièce.

        Disposition (vue de dessus, blancs en bas) :

            [N 2x4]  [  PLATEAU  ]  [N 2x4]    <- côté noir (rangs 7-8)
                     [           ]
                     [           ]
            [B 2x4]  [  PLATEAU  ]  [B 2x4]    <- côté blanc (rangs 1-2)

        - Pièces BLANCHES capturées : zones côté blanc (X bas), gauche puis droite
        - Pièces NOIRES capturées : zones côté noir (X haut), gauche puis droite
        - Chaque zone : 2 colonnes (Y) × 4 rangées (X) = 8 cases
        - Espacement : même que SQUARE_SIZE
        """
        # Charger l'état si disponible pour ne pas écraser les pièces précédentes après redémarrage
        self.load_state()

        spacing = self.SQUARE_SIZE  # Même espacement que le plateau
        board_size = self.SQUARE_SIZE * 8

        if is_white_piece:
            # Pièces BLANCHES capturées : côté blanc du plateau (rangs 1-2, X bas)
            count = self.white_capture_count

            # Zone gauche (0-7) puis zone droite (8-15)
            if count < 8:
                # Zone GAUCHE : Y < plateau, X aligné sur rangs 1-4
                zone = "gauche"
                local_index = count
                # 2 colonnes (Y) × 4 rangées (X)
                col = local_index % 2  # 0 ou 1 (colonne Y)
                row = local_index // 2  # 0 à 3 (rangée X)

                # Position : à gauche du plateau
                capture_y = self.BOARD_OFFSET_Y - spacing - (col * spacing)
                capture_x = self.BOARD_OFFSET_X + (row * spacing) + (spacing / 2)
            else:
                # Zone DROITE : Y > plateau, X aligné sur rangs 1-4
                zone = "droite"
                local_index = count - 8
                col = local_index % 2
                row = local_index // 2

                # Position : à droite du plateau
                capture_y = self.BOARD_OFFSET_Y + board_size + (col * spacing)
                capture_x = self.BOARD_OFFSET_X + (row * spacing) + (spacing / 2)

            self.white_capture_count += 1
            self.save_state()
            print(f"[CAPTURE] Pièce BLANCHE #{count+1} -> zone {zone} ({capture_x:.1f}, {capture_y:.1f})")

        else:
            # Pièces NOIRES capturées : côté noir du plateau (rangs 7-8, X haut)
            count = self.black_capture_count

            # Zone gauche (0-7) puis zone droite (8-15)
            if count < 8:
                # Zone GAUCHE : Y < plateau, X aligné sur rangs 5-8
                zone = "gauche"
                local_index = count
                col = local_index % 2
                row = local_index // 2

                # Position : à gauche du plateau, côté haut (rangs 5-8)
                capture_y = self.BOARD_OFFSET_Y - spacing - (col * spacing)
                capture_x = self.BOARD_OFFSET_X + board_size - (row * spacing) - (spacing / 2)
            else:
                # Zone DROITE : Y > plateau, X aligné sur rangs 5-8
                zone = "droite"
                local_index = count - 8
                col = local_index % 2
                row = local_index // 2

                # Position : à droite du plateau, côté haut
                capture_y = self.BOARD_OFFSET_Y + board_size + (col * spacing)
                capture_x = self.BOARD_OFFSET_X + board_size - (row * spacing) - (spacing / 2)

            self.black_capture_count += 1
            self.save_state()
            print(f"[CAPTURE] Pièce NOIRE #{count+1} -> zone {zone} ({capture_x:.1f}, {capture_y:.1f})")

        # Vérification des coordonnées négatives
        if capture_x < 0 or capture_y < 0:
            print(f"[WARNING] Coordonnée négative détectée! ({capture_x:.1f}, {capture_y:.1f})")
            print(f"[WARNING] Vérifiez board_offset_x/y dans robot_config.ini (min recommandé: {2*spacing:.1f}mm)")

        return (capture_x, capture_y)

    def load_state(self):
        """Charge les compteurs de capture depuis un fichier json."""
        state_file = "robot_state.json"
        if os.path.exists(state_file):
            try:
                import json
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    # On ne charge que si les compteurs actuels sont à 0 (démarrage du script)
                    if self.white_capture_count == 0 and self.black_capture_count == 0:
                        self.white_capture_count = data.get('white_count', 0)
                        self.black_capture_count = data.get('black_count', 0)
                        print(f"[STATE] État chargé: W={self.white_capture_count}, B={self.black_capture_count}")
            except Exception as e:
                print(f"[STATE] Erreur chargement état: {e}")

    def save_state(self):
        """Sauvegarde les compteurs de capture."""
        state_file = "robot_state.json"
        try:
            import json
            data = {
                'white_count': self.white_capture_count,
                'black_count': self.black_capture_count
            }
            with open(state_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[STATE] Erreur sauvegarde état: {e}")

    def remove_captured_piece(self, x: float, y: float, is_white_piece: bool = None, captured_piece_data: dict = None):
        """
        Retire une pièce capturée et la place dans la zone de capture à côté du plateau.

        Args:
            x, y: Coordonnées de la pièce à capturer
            is_white_piece: True si pièce blanche, False si noire, None pour auto-détection (obsolète)
            captured_piece_data: Données de la pièce (optionnel, pour mémoire)
        """
        # Si is_white_piece n'est pas fourni, utiliser l'ancien système (rétrocompatibilité)
        if is_white_piece is None:
            capture_x = self.CAPTURE_ZONE_X + (self.capture_count % 8) * self.CAPTURE_SPACING
            capture_y = self.CAPTURE_ZONE_Y + (self.capture_count // 8) * self.CAPTURE_SPACING
            self.capture_count += 1
        else:
            # Nouveau système : placer à côté du plateau selon la couleur
            capture_x, capture_y = self.get_capture_zone_position(is_white_piece)
            
        # Enregistrer dans la mémoire des pièces capturées
        if captured_piece_data:
            self.captured_pieces.append({
                'type': captured_piece_data['type'],
                'color': captured_piece_data['color'],
                'storage_pos': (capture_x, capture_y)
            })
            print(f"[MEMORY] Pièce ajoutée à la mémoire: {captured_piece_data['type']} {captured_piece_data['color']} -> ({capture_x:.1f}, {capture_y:.1f})")

        print(f"[ROBOT] Déplacement pièce capturée vers zone ({capture_x:.1f}, {capture_y:.1f})")

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
        Parse le format du fichier next_move.txt: {couleur};{mouvement};{capture}

        Args:
            move_line: Ligne du fichier (ex: "B;e2e4;0" ou "N;e4d5;1")

        Returns:
            Dictionnaire avec 'color', 'move' et 'is_capture', ou None si invalide

        Examples:
            "B;e2e4;0" -> {'color': 'B', 'move': 'e2e4', 'is_white': True, 'is_capture': False}
            "N;e4d5;1" -> {'color': 'N', 'move': 'e4d5', 'is_white': False, 'is_capture': True}
            "B;e2e4" -> {'color': 'B', 'move': 'e2e4', 'is_white': True, 'is_capture': False} (rétrocompatibilité)
        """
        try:
            parts = move_line.strip().split(';')
            if len(parts) < 2 or len(parts) > 3:
                print(f"[ERREUR] Format invalide: {move_line} (doit être 'couleur;mouvement' ou 'couleur;mouvement;capture')")
                return None

            color = parts[0].strip().upper()
            move = parts[1].strip().lower()

            # Nouveau: Gérer le flag de capture (si présent)
            is_capture = False
            if len(parts) == 3:
                capture_flag = parts[2].strip()
                is_capture = (capture_flag == '1')

            # Vérifier la couleur
            if color not in ['B', 'N', 'W']:  # B=Blanc, N=Noir, W=White
                print(f"[ERREUR] Couleur invalide: {color} (doit être B, N ou W)")
                return None

            # Vérifier le format du mouvement (au moins 4 caractères: e2e4)
            if len(move) < 4:
                print(f"[ERREUR] Mouvement invalide: {move}")
                return None

            return {
                'color': color,
                'move': move,
                'is_white': color in ['B', 'W'],
                'is_capture': is_capture
            }

        except Exception as e:
            print(f"[ERREUR] Erreur lors du parsing: {e}")
            return None

    def monitor_next_move_file(self, filename: str = "next_move.txt", callback=None, move_complete_event: Event = None):
        """
        Surveille le fichier next_move.txt et exécute les coups automatiquement et signale move_complete_event après chaque coup.
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
                                capture_status = "CAPTURE" if parsed['is_capture'] else "Déplacement"
                                print(f"[ROBOT] Couleur: {color_name}, Coup: {parsed['move']}, Type: {capture_status}")

                                # Exécuter le mouvement avec l'info de capture
                                self.execute_move(parsed['move'], is_capture=parsed['is_capture'])

                                if callback:
                                    callback(parsed)
                                # Signaler au thread principal que le mouvement est terminé.
                                if move_complete_event:
                                    print("[ROBOT] Mouvement terminé, envoi du signal de complétion.")
                                    move_complete_event.set()


                time.sleep(0.5)  # Vérifier toutes les 500ms

            except Exception as e:
                print(f"[ERREUR] Surveillance: {e}")
                time.sleep(1)

    def start_monitoring_next_move(self, filename: str = "next_move.txt", callback=None, event: Event = None):
        """
        Démarre la surveillance de next_move.txt dans un thread séparé.
        Accepte un 'event' pour la synchronisation.

        Args:
            filename: Nom du fichier à surveiller (défaut: next_move.txt)
            callback: Fonction appelée après chaque mouvement

        Returns:
            Le thread de surveillance
        """
        self.stop_monitoring.clear()
        monitor_thread = Thread(target=self.monitor_next_move_file,
                               args=(filename, callback, event))
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

    print("="*60)
    print("CONTRÔLEUR ROBOT D'ÉCHECS - G-CODE")
    print("="*60)

    # Créer le contrôleur (port et baudrate sont lus depuis robot_config.ini)
    robot = ChessRobotController()
    
    # 1. Tenter de se connecter
    if robot.connect():
        # 2. Si la connexion est réussie, lancer l'initialisation
        robot.home_robot()
    
        print("\nOptions:")
        print("1. Mode surveillance automatique (bestmove.txt)")
        print("2. Mode surveillance next_move.txt (format: couleur;mouvement)")
        print("3. Mode test manuel")
        print("4. Test pronation (servo)")
        print("5. Quitter")

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

        elif choice == '4':
            # Mode test pronation
            print("\n[INFO] Test de pronation du servo")
            print("[INFO] Commandes: 'n'=neutre, 'g'=gauche, 'd'=droite, 'angle'=valeur 0-180, 'quit'=quitter\n")

            while True:
                cmd = input("Commande (n/g/d/0-180/quit): ").strip().lower()

                if cmd == 'quit':
                    break
                elif cmd == 'n':
                    robot.pronation_neutral()
                elif cmd == 'g':
                    robot.pronation_left()
                elif cmd == 'd':
                    robot.pronation_right()
                else:
                    try:
                        angle = int(cmd)
                        robot.pronation_set_angle(angle)
                    except ValueError:
                        print("Commande invalide. Utilisez n/g/d ou un angle 0-180")
    else:
        # Si la connexion a échoué, afficher une erreur et arrêter
        print("\n[ERREUR FATALE] Impossible de continuer sans connexion au robot.")
        print("Vérifiez le port, le baudrate et le câble.")

    # Nettoyage
    robot.stop()
    print("\n[INFO] Programme terminé")


if __name__ == "__main__":
    main()
