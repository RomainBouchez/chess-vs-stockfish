"""
Intégration du robot avec le jeu d'échecs Chess vs Stockfish.
Ce fichier modifie chess_with_validation.py pour envoyer les coups au robot.
"""

import time
from robot_chess_controller import ChessRobotController

class ChessWithRobot:
    """
    Extension de la classe Chess pour intégrer le contrôle du robot.
    À utiliser en remplacement ou en extension de chess_with_validation.py
    """
    
    def __init__(self, enable_robot: bool = True, serial_port: str = 'COM3'):
        """
        Initialise le contrôle du robot.
        
        Args:
            enable_robot: Active/désactive le robot physique
            serial_port: Port série du robot
        """
        self.robot_enabled = enable_robot
        self.robot = None
        self.serial_port = serial_port
        self.last_move_sent = ""
        
        if self.robot_enabled:
            self.init_robot()
    
    def init_robot(self) -> bool:
        """Initialise la connexion avec le robot."""
        try:
            print("[ROBOT] Initialisation du contrôleur robot...")
            self.robot = ChessRobotController(port=self.serial_port, baudrate=115200)
            
            if self.robot.connect():
                print("[ROBOT] Robot connecté et prêt ✓")
                return True
            else:
                print("[ROBOT] Échec de connexion - Mode simulation")
                self.robot_enabled = False
                return False
                
        except Exception as e:
            print(f"[ROBOT] Erreur d'initialisation: {e}")
            self.robot_enabled = False
            return False
    
    def send_move_to_robot(self, move_uci: str, is_capture: bool = False, 
                          is_human: bool = False):
        """
        Envoie un coup au robot pour exécution physique.
        
        Args:
            move_uci: Coup au format UCI (ex: 'e2e4')
            is_capture: True si le coup capture une pièce
            is_human: True si c'est un coup humain (peut être ignoré par le robot)
        """
        if not self.robot_enabled or not self.robot:
            return
        
        # Éviter d'envoyer le même coup plusieurs fois
        if move_uci == self.last_move_sent:
            return
        
        self.last_move_sent = move_uci
        
        try:
            # Si on veut que le robot joue seulement les coups de Stockfish
            if is_human:
                print(f"[ROBOT] Coup humain détecté: {move_uci} - ignoré par le robot")
                # Vous devrez déplacer la pièce manuellement
                return
            
            print(f"\n[ROBOT] Envoi du coup à exécuter: {move_uci}")
            self.robot.execute_move(move_uci, is_capture)
            
        except Exception as e:
            print(f"[ROBOT] Erreur lors de l'exécution: {e}")
    
    def shutdown_robot(self):
        """Arrête proprement le robot."""
        if self.robot:
            print("[ROBOT] Arrêt du robot...")
            self.robot.stop()
            self.robot = None


# ==================== MODIFICATIONS POUR chess_with_validation.py ====================

def patch_chess_class():
    """
    Fonction pour patcher la classe Chess existante avec les fonctionnalités du robot.
    Ajouter ces modifications à chess_with_validation.py
    """
    modifications = """
    
# MODIFICATION 1: Ajouter l'import en haut du fichier
from chess_robot_integration import ChessWithRobot

# MODIFICATION 2: Dans __init__ de la classe Chess, ajouter:
def __init__(self, screen, pieces_src, square_coords, square_length):
    # ... code existant ...
    
    # NOUVEAU: Initialiser le robot
    self.robot_controller = ChessWithRobot(
        enable_robot=True,  # Mettre False pour désactiver
        serial_port='COM3'  # Adapter à votre configuration
    )

# MODIFICATION 3: Dans validate_and_apply_move (coups de Stockfish):
def validate_and_apply_move(self, move_uci):
    try:
        # ... code de validation existant ...
        
        # Appliquer le coup sur le board de validation
        self.validation_board.push(move)
        
        # NOUVEAU: Envoyer au robot (coup de Stockfish)
        is_capture = self.validation_board.is_capture(move)
        self.robot_controller.send_move_to_robot(
            move_uci, 
            is_capture=is_capture,
            is_human=False  # C'est Stockfish qui joue
        )
        
        # Appliquer le coup sur notre représentation interne
        return self.apply_move_to_internal_board(move_uci)
        
    except Exception as e:
        # ... gestion d'erreurs ...

# MODIFICATION 4: Dans validate_and_apply_human_move (coups du joueur):
def validate_and_apply_human_move(self, move_uci, from_file, from_rank, to_file, to_rank, piece_name):
    try:
        # ... code de validation existant ...
        
        # Le coup est légal, on peut l'appliquer
        self.validation_board.push(move)
        
        # OPTIONNEL: Envoyer au robot (coup humain)
        # Décommentez si vous voulez que le robot joue aussi vos coups
        # is_capture = target_piece != ""
        # self.robot_controller.send_move_to_robot(
        #     move_uci, 
        #     is_capture=is_capture,
        #     is_human=True
        # )
        
        # ... reste du code ...
        
    except Exception as e:
        # ... gestion d'erreurs ...

# MODIFICATION 5: Ajouter une méthode de nettoyage
def cleanup(self):
    '''Nettoie les ressources avant de fermer le jeu'''
    if hasattr(self, 'robot_controller'):
        self.robot_controller.shutdown_robot()

# MODIFICATION 6: Dans game_with_stockfish.py, modifier start_game():
# Dans la boucle while self.running:
for event in pygame.event.get():
    if event.type == pygame.QUIT or key_pressed[K_ESCAPE]:
        # NOUVEAU: Arrêter le robot proprement
        self.chess.cleanup()
        self.running = False
    """
    
    return modifications


# ==================== VERSION SIMPLIFIÉE POUR TEST ====================

class RobotMoveExecutor:
    """
    Version simplifiée qui lit bestmove.txt et exécute les coups.
    Utiliser en parallèle du jeu d'échecs existant.
    """
    
    def __init__(self, serial_port: str = 'COM3'):
        self.robot = ChessRobotController(port=serial_port, baudrate=115200)
        self.board_state = {}  # Dict pour suivre l'état du plateau
        self.init_board_state()
    
    def init_board_state(self):
        """Initialise l'état du plateau (position de départ)."""
        # Pièces blanches
        for file in 'abcdefgh':
            self.board_state[f"{file}2"] = "white_pawn"
        self.board_state.update({
            "a1": "white_rook", "h1": "white_rook",
            "b1": "white_knight", "g1": "white_knight",
            "c1": "white_bishop", "f1": "white_bishop",
            "d1": "white_queen", "e1": "white_king"
        })
        
        # Pièces noires
        for file in 'abcdefgh':
            self.board_state[f"{file}7"] = "black_pawn"
        self.board_state.update({
            "a8": "black_rook", "h8": "black_rook",
            "b8": "black_knight", "g8": "black_knight",
            "c8": "black_bishop", "f8": "black_bishop",
            "d8": "black_queen", "e8": "black_king"
        })
    
    def is_capture(self, move_uci: str) -> bool:
        """Détermine si un coup est une capture."""
        to_square = move_uci[2:4]
        return to_square in self.board_state
    
    def update_board_state(self, move_uci: str):
        """Met à jour l'état du plateau après un coup."""
        from_square = move_uci[:2]
        to_square = move_uci[2:4]
        
        if from_square in self.board_state:
            piece = self.board_state[from_square]
            self.board_state[to_square] = piece
            del self.board_state[from_square]
    
    def run(self):
        """Exécute la boucle principale."""
        if not self.robot.connect():
            print("[ERREUR] Impossible de se connecter au robot")
            return
        
        print("\n" + "="*60)
        print("ROBOT D'ÉCHECS - MODE AUTONOME")
        print("="*60)
        print("Le robot lit bestmove.txt et exécute les coups de Stockfish")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        last_move = ""
        last_modified = 0

        # Construire le chemin vers bestmove.txt dans le dossier parent
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        bestmove_path = os.path.join(parent_dir, "bestmove.txt")

        print(f"[INFO] Surveillance du fichier: {bestmove_path}")

        try:
            while True:
                if os.path.exists(bestmove_path):
                    current_modified = os.path.getmtime(bestmove_path)

                    if current_modified != last_modified:
                        last_modified = current_modified

                        with open(bestmove_path, 'r') as f:
                            move = f.read().strip()
                        
                        if move and move != last_move and len(move) >= 4:
                            last_move = move
                            
                            # Déterminer si c'est une capture
                            is_capture = self.is_capture(move)
                            
                            # Exécuter le mouvement
                            print(f"\n{'='*60}")
                            print(f"NOUVEAU COUP DÉTECTÉ: {move}")
                            if is_capture:
                                print("Type: CAPTURE")
                            print(f"{'='*60}\n")
                            
                            self.robot.execute_move(move, is_capture)
                            
                            # Mettre à jour l'état
                            self.update_board_state(move)
                            
                            print("\n[OK] Mouvement terminé - En attente du prochain coup...")
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n[INFO] Arrêt demandé par l'utilisateur")
        finally:
            self.robot.stop()
            print("[INFO] Robot arrêté proprement")


# ==================== POINT D'ENTRÉE ====================

if __name__ == "__main__":
    """
    Lancer ce script en parallèle de votre jeu d'échecs.
    Il lira bestmove.txt et enverra les coups au robot automatiquement.
    """
    
    import sys
    
    print("Choisissez le mode:")
    print("1. Mode autonome (lecture de bestmove.txt)")
    print("2. Afficher les modifications pour intégration")
    print("3. Quitter")
    
    choice = input("\nVotre choix: ")
    
    if choice == '1':
        # Demander le port série
        print("\nPorts série courants:")
        print("- Windows: COM3, COM4, COM5, ...")
        print("- Linux: /dev/ttyUSB0, /dev/ttyACM0, ...")
        print("- Mac: /dev/cu.usbserial, /dev/cu.usbmodem, ...")
        
        port = input("\nPort série (défaut: COM3): ").strip() or "COM3"
        
        executor = RobotMoveExecutor(serial_port=port)
        executor.run()
        
    elif choice == '2':
        print("\n" + "="*60)
        print("MODIFICATIONS POUR INTÉGRATION DANS chess_with_validation.py")
        print("="*60)
        print(patch_chess_class())
    
    else:
        print("Au revoir!")
