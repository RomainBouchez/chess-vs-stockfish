import pygame
import subprocess
import sys
import os
from game_with_stockfish import Game

# --- Constants for the menu ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 750
BLACK = (20, 20, 20)
WHITE = (220, 220, 220)
GREY = (80, 80, 80)
BUTTON_WIDTH = 400
BUTTON_HEIGHT = 70

def main_menu():
    """
    Displays the main menu and allows the user to select the game mode.
    Returns the selected mode ('pve' or 'pvp') or None if the user quits.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Chess - Main Menu")
    
    title_font = pygame.font.Font(None, 80)
    button_font = pygame.font.Font(None, 50)

    button_x = (SCREEN_WIDTH - BUTTON_WIDTH) // 2
    vs_ai_button = pygame.Rect(button_x, 300, BUTTON_WIDTH, BUTTON_HEIGHT)
    vs_player_button = pygame.Rect(button_x, 400, BUTTON_WIDTH, BUTTON_HEIGHT)

    running = True
    selected_mode = None

    while running:
        screen.fill(BLACK)
        title_text = title_font.render("Chess vs Stockfish", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_text, title_rect)

        pygame.draw.rect(screen, GREY, vs_ai_button, border_radius=10)
        ai_text = button_font.render("Play vs Stockfish", True, WHITE)
        ai_text_rect = ai_text.get_rect(center=vs_ai_button.center)
        screen.blit(ai_text, ai_text_rect)
        
        pygame.draw.rect(screen, GREY, vs_player_button, border_radius=10)
        player_text = button_font.render("Play 1v1 (2 Screens)", True, WHITE)
        player_text_rect = player_text.get_rect(center=vs_player_button.center)
        screen.blit(player_text, player_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if vs_ai_button.collidepoint(event.pos):
                    selected_mode = 'pve'
                    running = False
                if vs_player_button.collidepoint(event.pos):
                    selected_mode = 'pvp'
                    running = False
        pygame.display.flip()
    
    return selected_mode

def initialize_pvp_game_state():
    """Creates or clears the communication file for a new 1v1 game."""
    filename = "next_move.txt"
    try:
        # Start with an empty file. The white client will see this and know it's its turn.
        with open(filename, "w") as f:
            f.write("")
        print(f"'{filename}' has been cleared for the new 1v1 game.")
        return True
    except IOError as e:
        print(f"[CRITICAL ERROR] Could not initialize the game state file: {e}")
        return False

if __name__ == "__main__":
    game_mode = main_menu()

    if game_mode == 'pve':
        # For PVE, we run the game in the current process as before.
        # The player is always White in this mode.
        print("Starting Player vs AI game...")
        game = Game(mode='pve', player_color='WHITE')
        game.start_game()

    elif game_mode == 'pvp':
        # For PVP, we launch two new, separate processes.
        print("Launching Player vs Player mode...")
        
        # 1. Prepare the communication file
        if not initialize_pvp_game_state():
            pygame.quit()
            sys.exit(1)

        # 2. Get the path to the python interpreter and the script to run
        python_executable = sys.executable
        # The script to run is the one containing the Game class.
        script_to_run = "game_with_stockfish.py"

        try:
            # 3. Launch the two clients, passing 'pvp' mode and the player color as arguments
            print("Launching White player window...")
            subprocess.Popen([python_executable, script_to_run, 'pvp', 'WHITE'])
            
            print("Launching Black player window...")
            subprocess.Popen([python_executable, script_to_run, 'pvp', 'BLACK'])

        except Exception as e:
            print(f"[CRITICAL ERROR] Failed to launch game clients: {e}")
            pygame.quit()
            sys.exit(1)

    # The launcher's job is done, it can now close.
    print("Launcher is exiting.")
    pygame.quit()