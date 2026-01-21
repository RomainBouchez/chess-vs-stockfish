import os
import sys
import pygame
import chess
from pygame.locals import *
from threading import Event

try:
    from chess_with_validation import Chess
    from utils import Utils
    from settings_menu import SettingsMenu
    from settings import StockfishSettings
    from bot_selection_menu import BotSelectionMenu
except ImportError as e:
    print(f"[ERROR] A required module is missing: {e}")
    print("Please ensure all game files (chess_with_validation.py, utils.py, etc.) are in the same directory.")
    sys.exit(1)


class Game:
    def __init__(self, mode='pve', player_color='WHITE', enable_robot=False):
        self.mode = mode
        self.player_color = player_color.upper()
        self.running = True
        self.enable_robot = enable_robot
        self.robot_controller = None
        self.robot_thread = None
        self.robot_move_complete_event = Event()

        screen_width = 640
        screen_height = 750
        self.resources = "res"
        pygame.init()
        self.screen = pygame.display.set_mode([screen_width, screen_height])
        self.clock = pygame.time.Clock()

        if self.mode == 'pvp':
            window_title = f"Chess 1v1 - {self.player_color.title()} Player"
        else:
            # Keep the player_color passed by the caller (default is WHITE)
            if not self.player_color:
                self.player_color = 'WHITE'
            window_title = f"Chess vs Stockfish - You play as {self.player_color.title()}"
        pygame.display.set_caption(window_title)

        try:
            icon_src = os.path.join(self.resources, "chess_icon.png")
            icon = pygame.image.load(icon_src)
            pygame.display.set_icon(icon)
        except pygame.error:
            print(f"Warning: Icon file not found at '{icon_src}'")

        if self.mode == 'pvp':
            self.move_file = "next_move.txt"
            self.last_read_move = self.read_last_move()
            self.is_my_turn = (self.player_color == 'WHITE' and not self.last_read_move)
        
        self.menu_showed = self.mode == 'pvp'

    def read_last_move(self):
        if not os.path.exists(self.move_file): return ""
        try:
            with open(self.move_file, "r") as f: return f.read().strip()
        except IOError: return ""

    def init_robot(self):
        """Initialise et démarre le robot pour exécuter les coups physiquement."""
        try:
            # Import local pour éviter les erreurs si le module n'existe pas
            import sys
            robot_path = os.path.join(os.path.dirname(__file__), 'G-Code_Controller')
            if robot_path not in sys.path:
                sys.path.insert(0, robot_path)

            from robot_chess_controller import ChessRobotController

            print("\n" + "="*60)
            print("INITIALISATION DU ROBOT")
            print("="*60)

            # Demander le port série (ou utiliser une config par défaut)
            # Pour l'instant, on utilise COM3 par défaut
            # TODO: Ajouter une config ou un menu de sélection
            self.robot_controller = ChessRobotController(port='COM3', baudrate=115200)

            if self.robot_controller.connect():
                print("[ROBOT] Connexion réussie !")
                self.robot_controller.home_robot()

                # Démarrer la surveillance du fichier next_move.txt
                print("[ROBOT] Démarrage de la surveillance de next_move.txt...")
                self.robot_thread = self.robot_controller.start_monitoring_next_move(
                    filename="next_move.txt",
                    callback=self.on_robot_move_complete,
                    event=self.robot_move_complete_event
                )
                print("[ROBOT] Robot prêt à jouer ! ✓")
            else:
                print("[ERREUR] Impossible de se connecter au robot")
                self.enable_robot = False
                self.robot_controller = None

        except Exception as e:
            print(f"[ERREUR] Initialisation robot échouée: {e}")
            import traceback
            traceback.print_exc()
            self.enable_robot = False
            self.robot_controller = None

    def on_robot_move_complete(self, parsed_move):
        """Callback appelé quand le robot termine un coup."""
        color_name = "Blanc" if parsed_move['is_white'] else "Noir"
        print(f"[CALLBACK] {color_name} - {parsed_move['move']} terminé")

    def wait_for_robot_move(self, timeout=30):
        """
        Attend que le robot termine le coup en cours.

        Args:
            timeout: Temps d'attente maximum en secondes (défaut: 30s)

        Returns:
            True si le robot a terminé, False si timeout
        """
        if not self.enable_robot or not self.robot_controller:
            return True  # Pas de robot, on continue

        print("[SYNC] Attente que le robot termine le coup...")
        result = self.robot_move_complete_event.wait(timeout=timeout)

        if result:
            print("[SYNC] Robot a terminé le coup ✓")
            # Réinitialiser l'event pour le prochain coup
            self.robot_move_complete_event.clear()
        else:
            print(f"[ERREUR] Timeout: le robot n'a pas terminé en {timeout}s")

        return result

    def stop_robot(self):
        """Arrête proprement le robot."""
        if self.robot_controller:
            print("\n[ROBOT] Arrêt du robot...")
            self.robot_controller.stop()
            self.robot_controller = None

    def start_game(self):
        self.board_offset_x, self.board_offset_y = 0, 50
        self.board_dimensions = (self.board_offset_x, self.board_offset_y)
        
        try:
            board_src = os.path.join(self.resources, "board.png")
            self.board_img = pygame.image.load(board_src).convert()
        except pygame.error:
            self.board_img = pygame.Surface((480, 480))
            for r in range(8):
                for c in range(8):
                    color = (240, 217, 181) if (r + c) % 2 == 0 else (181, 136, 99)
                    pygame.draw.rect(self.board_img, color, (c * 60, r * 60, 60, 60))

        square_length = self.board_img.get_rect().width // 8
        self.board_locations = [
            [[self.board_offset_x + (c * square_length), self.board_offset_y + (r * square_length)] for r in range(8)] for c in range(8)
        ]

        pieces_src = os.path.join(self.resources, "pieces.png")

        # Passer le callback d'attente robot si le robot est activé
        robot_wait_callback = self.wait_for_robot_move if self.enable_robot else None
        self.chess = Chess(self.screen, pieces_src, self.board_locations, square_length, self.mode, self.player_color, robot_wait_callback)

        # Initialiser le robot si activé
        if self.enable_robot:
            self.init_robot()

        while self.running:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    self.running = False
                if event.type == KEYDOWN and event.key == K_SPACE and self.mode == 'pve':
                    self.chess.reset()
                    self.menu_showed = False

            winner = self.chess.get_winner()

            if not self.menu_showed:
                self.pve_menu()
            elif winner:
                self.declare_winner(winner)
            else:
                self.game()

            pygame.display.flip()
        pygame.quit()

    def check_for_opponent_move(self):
        current_move_in_file = self.read_last_move()
        if current_move_in_file and current_move_in_file != self.last_read_move:
            self.last_read_move = current_move_in_file
            try:
                player, move_uci, capture_flag = current_move_in_file.split(';')
                opponent_color = 'BLACK' if self.player_color == 'WHITE' else 'WHITE'
                if player == opponent_color[0]:
                    print(f"[{self.player_color}] Detected opponent's move: {move_uci}")
                    if self.chess.validate_and_apply_move(move_uci):
                        self.is_my_turn = True
            except ValueError:
                print(f"[{self.player_color}] WARNING: Malformed move in file: '{current_move_in_file}'")

    def draw_captured_pieces(self):
        """Affiche les pièces capturées sur le côté du plateau."""
        # Note: self.chess.white_captured contient les pièces NOIRES capturées (par les blancs)
        # Note: self.chess.black_captured contient les pièces BLANCHES capturées (par les noirs)

        # Taille réduite pour les pièces capturées
        piece_size = 30
        x_offset = 500  # Position à droite du plateau
        
        # --- Affichage des pièces NOIRES (capturées) en HAUT ---
        y_black = 60
        # Dessiner une grille vide 4x4 pour matérialiser les emplacements
        for i in range(16):
            col = i % 4
            row = i // 4
            rect = (x_offset + col * piece_size, y_black + row * piece_size, piece_size, piece_size)
            pygame.draw.rect(self.screen, (60, 60, 60), rect, 1) # Cadre gris foncé

        # Afficher les pièces dans l'ordre de capture (PAS DE TRI)
        for i, piece_name in enumerate(self.chess.white_captured):
            if i >= 16: break # Sécurité dépassement grille
            x_pos = x_offset + (i % 4) * piece_size
            y_pos = y_black + (i // 4) * piece_size
            scaled_pos = (x_pos, y_pos)
            
            # Récupérer l'index de la pièce et l'afficher
            if piece_name in self.chess.chess_pieces.pieces:
                piece_index = self.chess.chess_pieces.pieces[piece_name]
                cell = self.chess.chess_pieces.cells[piece_index]
                piece_img = self.chess.chess_pieces.spritesheet.subsurface(cell)
                piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                self.screen.blit(piece_img, scaled_pos)

        # --- Affichage des pièces BLANCHES (capturées) en BAS ---
        # Ajusté à 550 pour éviter que ça sorte de l'écran (750px)
        y_white = 550
        # Dessiner une grille vide 4x4
        for i in range(16):
            col = i % 4
            row = i // 4
            rect = (x_offset + col * piece_size, y_white + row * piece_size, piece_size, piece_size)
            pygame.draw.rect(self.screen, (60, 60, 60), rect, 1)

        # Afficher les pièces dans l'ordre de capture
        for i, piece_name in enumerate(self.chess.black_captured):
            if i >= 16: break
            x_pos = x_offset + (i % 4) * piece_size
            y_pos = y_white + (i // 4) * piece_size
            scaled_pos = (x_pos, y_pos)
            
            if piece_name in self.chess.chess_pieces.pieces:
                piece_index = self.chess.chess_pieces.pieces[piece_name]
                cell = self.chess.chess_pieces.cells[piece_index]
                piece_img = self.chess.chess_pieces.spritesheet.subsurface(cell)
                piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                self.screen.blit(piece_img, scaled_pos)

    def game(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.board_img, self.board_dimensions)
        is_flipped = (self.player_color == 'BLACK')
        turn_font = pygame.font.SysFont("sans-serif", 24)
        status_text = ""
        
        # Variable pour savoir si on doit attendre le robot après cette frame
        move_made_this_frame = False

        if self.mode == 'pvp':
            if not self.is_my_turn: self.check_for_opponent_move()
            status_text = "Your Turn" if self.is_my_turn else "Waiting for Opponent..."
            if self.is_my_turn:
                # handle_human_move retourne True si un coup est joué
                if self.chess.handle_human_move(self.player_color.lower(), is_flipped):
                    self.last_read_move = self.read_last_move()
                    self.is_my_turn = False
                    move_made_this_frame = True
        else: # PVE Mode
            human_is_white = (self.player_color == 'WHITE')
            board_turn_is_white = (self.chess.validation_board.turn == chess.WHITE)
            is_human_turn = (human_is_white and board_turn_is_white) or (not human_is_white and not board_turn_is_white)

            status_text = "Your Turn" if is_human_turn else "Stockfish is thinking..."
            
            # play_turn_pve retourne True si un coup a été joué (par le joueur ou l'IA)
            if self.chess.play_turn_pve():
                move_made_this_frame = True

        # --- NOUVEAU BLOC DE SYNCHRONISATION AVEC LE ROBOT ---
        if self.enable_robot and move_made_this_frame:
            # 1. Préparer le signal pour la prochaine attente
            self.robot_move_complete_event.clear()

            # 2. Afficher un message d'attente à l'écran
            wait_text = "Robot is moving..."
            wait_surf = turn_font.render(wait_text, True, (255, 255, 0)) # Jaune
            
            # Dessiner le reste de l'écran pour que tout soit à jour
            self.chess.draw_pieces(is_flipped)
            self.draw_captured_pieces()
            self.screen.blit(wait_surf, ((self.screen.get_width() - wait_surf.get_width()) // 2, 15))
            pygame.display.flip() # Forcer la mise à jour de l'écran avec le message

            # 3. Mettre le jeu en pause et attendre le signal du robot
            print("[GAME] Un coup a été joué. Mise en pause du jeu en attente du robot...")
            # Le .wait() bloque l'exécution jusqu'à ce que l'event soit .set() par le robot
            self.robot_move_complete_event.wait(timeout=60.0) # Timeout de 60s par sécurité
            print("[GAME] Signal du robot reçu. Le jeu reprend.")

        # Affichage normal du statut (sera écrasé par le message d'attente si nécessaire)
        text_surface = turn_font.render(status_text, True, (255, 255, 255))
        self.screen.blit(text_surface, ((self.screen.get_width() - text_surface.get_width()) // 2, 15))
        
        # Redessiner le tout au cas où l'écran n'a pas été mis à jour pendant l'attente
        self.chess.draw_pieces(is_flipped)
        self.draw_captured_pieces()

    # --- UI UPDATED: This function has been redesigned ---
    def pve_menu(self):
        """Shows the pre-game menu for PVE mode with a modern UI."""
        # --- UI Style Constants ---
        SCREEN_WIDTH = self.screen.get_width()
        BLACK = (20, 20, 20)
        WHITE = (220, 220, 220)
        GREY = (80, 80, 80)
        LIGHT_GREY = (170, 170, 170)
        BUTTON_WIDTH = 400
        BUTTON_HEIGHT = 70

        # --- Fonts (using default Pygame font for consistency) ---
        title_font = pygame.font.Font(None, 70)
        subtitle_font = pygame.font.Font(None, 35)
        elo_font = pygame.font.Font(None, 28)
        button_font = pygame.font.Font(None, 50)
        
        # --- Screen Background ---
        self.screen.fill(BLACK)
        
        # --- Get Engine Info ---
        from universal_engine import get_universal_engine
        engine = get_universal_engine()
        engine_info = engine.get_engine_info()
        title_text_str = f"Chess vs {engine_info['name']}" if engine_info['name'] else "Chess vs AI"
        pygame.display.set_caption(title_text_str)

        from universal_settings import UniversalEngineSettings
        universal_settings = UniversalEngineSettings()
        current_elo = universal_settings.get_elo_for_engine()

        # --- Render Text Surfaces ---
        title_surf = title_font.render(title_text_str, True, WHITE)
        subtitle_surf = subtitle_font.render("You play as White", True, LIGHT_GREY)
        elo_surf = elo_font.render(f"Engine Level: {current_elo} ELO", True, LIGHT_GREY)
        play_btn_surf = button_font.render("Play", True, WHITE)
        settings_btn_surf = button_font.render("Settings", True, WHITE)

        # --- Create Button Rects ---
        button_x = (SCREEN_WIDTH - BUTTON_WIDTH) // 2
        play_btn_rect = pygame.Rect(button_x, 300, BUTTON_WIDTH, BUTTON_HEIGHT)
        settings_btn_rect = pygame.Rect(button_x, 400, BUTTON_WIDTH, BUTTON_HEIGHT)
        
        # --- Draw Buttons ---
        pygame.draw.rect(self.screen, GREY, play_btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, GREY, settings_btn_rect, border_radius=10)

        # --- Blit All Elements (Centered) ---
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120)))
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 180)))
        self.screen.blit(elo_surf, elo_surf.get_rect(center=(SCREEN_WIDTH // 2, 220)))
        self.screen.blit(play_btn_surf, play_btn_surf.get_rect(center=play_btn_rect.center))
        self.screen.blit(settings_btn_surf, settings_btn_surf.get_rect(center=settings_btn_rect.center))

        # --- Event Handling ---
        util = Utils()
        if util.left_click_event():
            mouse_coords = util.get_mouse_event()
            if play_btn_rect.collidepoint(mouse_coords):
                self.menu_showed = True
            elif settings_btn_rect.collidepoint(mouse_coords):
                # Use the new Bot Selection Menu
                bot_menu = BotSelectionMenu(self.screen)
                action = bot_menu.run()
                if action == "play":
                    self.menu_showed = True
                
        elif pygame.key.get_pressed()[K_RETURN]:
            self.menu_showed = True

    def declare_winner(self, winner):
        self.screen.fill((255, 255, 255))
        big_font = pygame.font.SysFont("sans-serif", 60)
        
        if winner == "Draw": text = "Draw!"
        elif winner.upper() == self.player_color: text = "You Win!"
        else: text = "You Lose!"
            
        winner_text = big_font.render(text, True, (0, 0, 0))
        self.screen.blit(winner_text, ((self.screen.get_width() - winner_text.get_width()) // 2, 150))
        small_font = pygame.font.SysFont("sans-serif", 20)
        esc_text = small_font.render("Press ESC to close this window", True, (50,50,50))
        self.screen.blit(esc_text, ((self.screen.get_width() - esc_text.get_width()) // 2, 300))

if __name__ == "__main__":
    game_mode = 'pve'
    player_color = 'WHITE'
    if len(sys.argv) > 2:
        game_mode = sys.argv[1].lower()
        player_color = sys.argv[2].upper()
    
    print(f"Starting game instance with Mode: {game_mode}, Color: {player_color}")
    game = Game(mode=game_mode, player_color=player_color)
    game.start_game()