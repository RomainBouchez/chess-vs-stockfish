import chess
import chess.engine
import sys
import os

# Add parent directory to path to import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from universal_engine import get_universal_engine
    # Wrapper for robot controller imports
    # Handle G-Code_Controller directory with dashes
    gcode_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "G-Code_Controller")
    if gcode_path not in sys.path:
        sys.path.append(gcode_path)
    from robot_chess_controller import ChessRobotController
except ImportError as e:
    print(f"[WARNING] Could not import dependencies: {e}")
    ChessRobotController = None


# ==================== DEBUG PROXY (TEMPORARY) ====================
class RobotDebugProxy(ChessRobotController):
    """
    DEBUG ONLY - Simulates the robot without serial connection.
    Collects all GCode commands that would be sent.
    Remove this class after debugging.
    """

    def __init__(self):
        self._debug_log = []
        # Initialize parent with config but no serial
        super().__init__()

    def connect(self) -> bool:
        self.is_connected = True
        self._debug_log.append("[DEBUG] Robot simulé connecté (pas de serial)")
        print("[DEBUG-ROBOT] Proxy debug initialisé - aucune connexion série")
        return True

    def disconnect(self):
        self.is_connected = False
        self._debug_log.append("[DEBUG] Robot simulé déconnecté")

    def send_command(self, command: str, wait_ok: bool = True) -> bool:
        self._debug_log.append(f"GCODE >>> {command}")
        print(f"[DEBUG-ROBOT] GCODE >>> {command}")
        return True

    def grab_piece(self):
        self._debug_log.append(f"GCODE >>> {self.GRAB_COMMAND}  (grab)")
        print(f"[DEBUG-ROBOT] GCODE >>> {self.GRAB_COMMAND}  (grab)")

    def release_piece(self):
        self._debug_log.append(f"GCODE >>> {self.RELEASE_COMMAND}  (release)")
        print(f"[DEBUG-ROBOT] GCODE >>> {self.RELEASE_COMMAND}  (release)")

    def move_to_position(self, x: float, y: float, z: float, feed_rate: int = None):
        if feed_rate:
            xy_cmd = f"G0 X{x:.2f} Y{y:.2f} F{feed_rate}"
        else:
            xy_cmd = f"G0 X{x:.2f} Y{y:.2f}"
        self._debug_log.append(f"GCODE >>> {xy_cmd}")
        print(f"[DEBUG-ROBOT] GCODE >>> {xy_cmd}")

        # Z axis
        if self.Z_UP_COMMAND.startswith('G0') or self.Z_UP_COMMAND.startswith('G1'):
            z_cmd = f"G0 Z{z:.2f} F{self.FEED_RATE_TRAVEL}"
        else:
            z_cmd = self.Z_DOWN_COMMAND if z <= self.Z_GRAB else self.Z_UP_COMMAND
        self._debug_log.append(f"GCODE >>> {z_cmd}")
        print(f"[DEBUG-ROBOT] GCODE >>> {z_cmd}")

    def home_robot(self):
        self._debug_log.append("GCODE >>> G28 X Y  (homing)")
        self._debug_log.append(f"GCODE >>> G0 Z{self.Z_SAFE}  (safe height)")
        self._debug_log.append(f"GCODE >>> G0 X{self.BOARD_OFFSET_X} Y{self.BOARD_OFFSET_Y}  (go to a1)")
        print("[DEBUG-ROBOT] home_robot() simulé")

    def flush_debug_log(self):
        """Returns and clears the debug log."""
        log = list(self._debug_log)
        self._debug_log.clear()
        return log

    def save_state(self):
        pass  # Don't write state files in debug mode

    def load_state(self):
        pass  # Don't read state files in debug mode
# ==================== END DEBUG PROXY ====================


class GameManager:
    def __init__(self, enable_robot=False):
        self.board = chess.Board()
        self.engine = get_universal_engine()
        self.robot = None
        self.enable_robot = enable_robot
        self.white_captured = []
        self.black_captured = []

        # DEBUG: Always create a debug proxy to log GCode commands
        self.debug_robot = None
        if ChessRobotController:
            try:
                self.debug_robot = RobotDebugProxy()
                self.debug_robot.connect()
                print("[DEBUG] RobotDebugProxy actif - toutes les commandes seront loguées")
            except Exception as e:
                print(f"[DEBUG] Impossible de créer le debug proxy: {e}")

        # Initialize Engine
        if not self.engine.initialize():
            print("[WARNING] Stockfish engine could not be initialized.")

        # Initialize Robot
        if self.enable_robot and ChessRobotController:
            try:
                self.robot = ChessRobotController(port='COM3') # Default port, consideration to make configurable needed
                if self.robot.connect():
                    self.robot.home_robot()
                else:
                    self.robot = None
                    print("[WARNING] Robot connection failed.")
            except Exception as e:
                print(f"[ERROR] Robot initialization failed: {e}")
                self.robot = None

    def reset_game(self):
        self.board.reset()
        self.white_captured = []
        self.black_captured = []
        if self.robot:
            # Optional: Move robot to home or reset state?
            # self.robot.home_robot() # Might be too slow to do every game
            pass 
        return self.get_state()

    def get_state(self):
        return {
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_game_over": self.board.is_game_over(),
            "winner": self._get_winner(),
            "white_captured": self.white_captured,
            "black_captured": self.black_captured
        }

    def _get_winner(self):
        if not self.board.is_game_over():
            return None
        if self.board.is_checkmate():
            return "black" if self.board.turn == chess.WHITE else "white"
        return "draw"

    def apply_move(self, uci_move):
        """
        Applies a move (UCI string).
        Returns: (success, state_dict, debug_log)
        """
        if not uci_move or not isinstance(uci_move, str):
            return False, self.get_state(), []
        try:
            move = chess.Move.from_uci(uci_move)
            if move in self.board.legal_moves:
                # Capture logic detection
                is_capture = self.board.is_capture(move) or self.board.is_en_passant(move)

                # Update captured lists manually for frontend display (approximate)
                if is_capture:
                    if self.board.is_en_passant(move):
                        captured_piece = chess.PAWN
                    else:
                        captured_piece = self.board.piece_at(move.to_square).piece_type

                    piece_char = chess.piece_symbol(captured_piece)
                    if self.board.turn == chess.WHITE:
                        self.black_captured.append(piece_char) # White captured a black piece
                    else:
                        self.white_captured.append(piece_char) # Black captured a white piece

                turn_color = "white" if self.board.turn == chess.WHITE else "black"
                self.board.push(move)

                # Trigger Robot if valid
                if self.robot:
                    try:
                        self.robot.execute_move(uci_move, is_capture)
                    except Exception as e:
                        print(f"[ERROR] Robot Error: {e}")

                # DEBUG: Always run debug proxy to log GCode commands
                debug_log = []
                if self.debug_robot:
                    try:
                        self.debug_robot.flush_debug_log()  # Clear previous
                        self.debug_robot.execute_move(uci_move, is_capture)
                        debug_log = self.debug_robot.flush_debug_log()
                        # Prepend move summary
                        move_type = "capture" if is_capture else "move"
                        debug_log.insert(0, f"--- {turn_color} {move_type}: {uci_move} ---")
                        debug_log.append(f"--- robot connecté: {self.robot is not None} ---")
                    except Exception as e:
                        debug_log = [f"[DEBUG ERROR] {e}"]

                return True, self.get_state(), debug_log
            else:
                return False, self.get_state(), []
        except ValueError:
            return False, self.get_state(), []

    def get_best_move(self):
        """Returns best move from Stockfish for current position."""
        if not self.engine:
            return None
        return self.engine.get_best_move(self.board.fen())

    def get_settings(self):
        """Get current engine settings"""
        if self.engine:
            return self.engine.get_settings()
        return {}

    def update_settings(self, settings):
        """Update engine settings"""
        if self.engine:
            # For now only ELO support
            elo = settings.get("elo")
            return self.engine.apply_settings(elo=elo)
        return False

    def disconnect(self):
        if self.robot:
            self.robot.disconnect()
        if self.engine:
            self.engine.quit()
