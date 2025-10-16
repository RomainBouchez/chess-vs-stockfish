import os
import sys
import pygame
import chess
from pygame.locals import *

try:
    from chess_with_validation import Chess
    from utils import Utils
    from settings_menu import SettingsMenu
    from settings import StockfishSettings
except ImportError as e:
    print(f"[ERROR] A required module is missing: {e}")
    print("Please ensure all game files (chess_with_validation.py, utils.py, etc.) are in the same directory.")
    sys.exit(1)


class Game:
    def __init__(self, mode='pve', player_color='WHITE'):
        self.mode = mode
        self.player_color = player_color.upper()
        self.running = True
        
        screen_width = 640
        screen_height = 750
        self.resources = "res"
        pygame.init()
        self.screen = pygame.display.set_mode([screen_width, screen_height])
        self.clock = pygame.time.Clock()

        if self.mode == 'pvp':
            window_title = f"Chess 1v1 - {self.player_color.title()} Player"
        else:
            self.player_color = 'WHITE'
            window_title = "Chess vs Stockfish"
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
        self.chess = Chess(self.screen, pieces_src, self.board_locations, square_length, self.mode, self.player_color)

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
                player, move_uci = current_move_in_file.split(';')
                opponent_color = 'BLACK' if self.player_color == 'WHITE' else 'WHITE'
                if player == opponent_color[0]:
                    print(f"[{self.player_color}] Detected opponent's move: {move_uci}")
                    if self.chess.validate_and_apply_move(move_uci):
                        self.is_my_turn = True
            except ValueError:
                print(f"[{self.player_color}] WARNING: Malformed move in file: '{current_move_in_file}'")

    def game(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.board_img, self.board_dimensions)
        is_flipped = (self.player_color == 'BLACK')
        turn_font = pygame.font.SysFont("sans-serif", 24)
        status_text = ""

        if self.mode == 'pvp':
            if not self.is_my_turn: self.check_for_opponent_move()
            status_text = "Your Turn" if self.is_my_turn else "Waiting for Opponent..."
            if self.is_my_turn:
                if self.chess.handle_human_move(self.player_color.lower(), is_flipped):
                    self.last_read_move = self.read_last_move()
                    self.is_my_turn = False
        else: # PVE Mode
            status_text = "Your Turn" if self.chess.turn["white"] else "Stockfish is thinking..."
            self.chess.play_turn_pve()

        text_surface = turn_font.render(status_text, True, (255, 255, 255))
        self.screen.blit(text_surface, ((self.screen.get_width() - text_surface.get_width()) // 2, 15))
        self.chess.draw_pieces(is_flipped)

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
                settings_menu = SettingsMenu(self.screen)
                settings_menu.run()
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