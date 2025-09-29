import os
import pygame
from pygame.locals import *
from piece import Piece
from chess_with_validation import Chess
from utils import Utils
from settings_menu import SettingsMenu
from settings import StockfishSettings

class Game:
    def __init__(self):
        # screen dimensions
        screen_width = 640
        screen_height = 750
        # flag to know if game menu has been showed
        self.menu_showed = False
        # flag to set game loop
        self.running = True
        # base folder for program resources
        self.resources = "res"
        
        # Paramètres Stockfish
        self.stockfish_settings = StockfishSettings()
 
        # initialize game window
        pygame.display.init()
        # initialize font for text
        pygame.font.init()

        # create game window
        self.screen = pygame.display.set_mode([screen_width, screen_height])

        # title of window
        window_title = "Chess vs Stockfish"
        # set window caption
        pygame.display.set_caption(window_title)

        # get location of game icon
        icon_src = os.path.join(self.resources, "chess_icon.png")
        # load game icon (si disponible)
        try:
            icon = pygame.image.load(icon_src)
            pygame.display.set_icon(icon)
        except:
            pass  # Ignore if icon file doesn't exist
            
        # update display
        pygame.display.flip()
        # set game clock
        self.clock = pygame.time.Clock()


    def start_game(self):
        """Function containing main game loop""" 
        # chess board offset
        self.board_offset_x = 0
        self.board_offset_y = 50
        self.board_dimensions = (self.board_offset_x, self.board_offset_y)
        
        # get location of chess board image
        board_src = os.path.join(self.resources, "board.png")
        
        # load the chess board image (ou créer un plateau simple si pas d'image)
        try:
            self.board_img = pygame.image.load(board_src).convert()
        except:
            # Créer un plateau simple si l'image n'existe pas
            self.board_img = pygame.Surface((480, 480))
            for row in range(8):
                for col in range(8):
                    color = (240, 217, 181) if (row + col) % 2 == 0 else (181, 136, 99)
                    pygame.draw.rect(self.board_img, color, 
                                   (col * 60, row * 60, 60, 60))

        # get the width of a chess board square
        square_length = self.board_img.get_rect().width // 8

        # initialize list that stores all places to put chess pieces on the board
        self.board_locations = []

        # calculate coordinates of the each square on the board
        for x in range(0, 8):
            self.board_locations.append([])
            for y in range(0, 8):
                self.board_locations[x].append([self.board_offset_x+(x*square_length), 
                                                self.board_offset_y+(y*square_length)])

        # get location of image containing the chess pieces
        pieces_src = os.path.join(self.resources, "pieces.png")
        # create class object that handles the gameplay logic
        self.chess = Chess(self.screen, pieces_src, self.board_locations, square_length)

        # game loop
        while self.running:
            self.clock.tick(60)  # 60 FPS pour une meilleure réactivité
            # poll events
            for event in pygame.event.get():
                # get keys pressed
                key_pressed = pygame.key.get_pressed()
                # check if the game has been closed by the user
                if event.type == pygame.QUIT or key_pressed[K_ESCAPE]:
                    # set flag to break out of the game loop
                    self.running = False
                elif key_pressed[K_SPACE]:
                    self.chess.reset()
            
            winner = self.chess.winner

            if self.menu_showed == False:
                self.menu()
            elif len(winner) > 0:
                self.declare_winner(winner)
            else:
                self.game()

            # update display
            pygame.display.flip()
            # update events
            pygame.event.pump()

        # call method to stop pygame
        pygame.quit()
    

    def menu(self):
        """method to show game menu"""
        # background color
        bg_color = (255, 255, 255)
        # set background color
        self.screen.fill(bg_color)
        # black color
        black_color = (0, 0, 0)
        
        # Boutons du menu
        start_btn = pygame.Rect(220, 280, 200, 50)
        settings_btn = pygame.Rect(220, 350, 200, 50)
        
        # Dessiner les boutons
        pygame.draw.rect(self.screen, black_color, start_btn)
        pygame.draw.rect(self.screen, (50, 100, 200), settings_btn)

        # white color
        white_color = (255, 255, 255)
        # create fonts for texts
        big_font = pygame.font.SysFont("comicsansms", 50)
        medium_font = pygame.font.SysFont("comicsansms", 30)
        small_font = pygame.font.SysFont("comicsansms", 20)
        tiny_font = pygame.font.SysFont("comicsansms", 16)
        
        # create text to be shown on the game menu
        welcome_text = big_font.render("Chess vs Stockfish", False, black_color)
        subtitle_text = medium_font.render("You play White", False, black_color)
        
        # Afficher l'ELO actuel
        current_elo = self.stockfish_settings.get_elo()
        elo_text = tiny_font.render(f"Niveau Stockfish: {current_elo} ELO", True, (100, 100, 100))
        
        created_by = small_font.render("Human vs AI", True, black_color)
        start_btn_label = small_font.render("Play", True, white_color)
        settings_btn_label = small_font.render("Settings", True, white_color)
        
        # show welcome text
        self.screen.blit(welcome_text, 
                      ((self.screen.get_width() - welcome_text.get_width()) // 2, 
                      100))
        # show subtitle text
        self.screen.blit(subtitle_text, 
                      ((self.screen.get_width() - subtitle_text.get_width()) // 2, 
                      160))
        
        # Afficher ELO
        self.screen.blit(elo_text, 
                      ((self.screen.get_width() - elo_text.get_width()) // 2, 
                      220))
        
        # show credit text
        self.screen.blit(created_by, 
                      ((self.screen.get_width() - created_by.get_width()) // 2, 
                      self.screen.get_height() - created_by.get_height() - 100))
        
        # show text on buttons
        self.screen.blit(start_btn_label, 
                      ((start_btn.x + (start_btn.width - start_btn_label.get_width()) // 2, 
                      start_btn.y + (start_btn.height - start_btn_label.get_height()) // 2)))
        
        self.screen.blit(settings_btn_label, 
                      ((settings_btn.x + (settings_btn.width - settings_btn_label.get_width()) // 2, 
                      settings_btn.y + (settings_btn.height - settings_btn_label.get_height()) // 2)))

        # get pressed keys
        key_pressed = pygame.key.get_pressed()
        # 
        util = Utils()

        # check if left mouse button was clicked
        if util.left_click_event():
            # call function to get mouse event
            mouse_coords = util.get_mouse_event()

            # check if "Play" button was clicked
            if start_btn.collidepoint(mouse_coords[0], mouse_coords[1]):
                # change button behavior as it is hovered
                pygame.draw.rect(self.screen, white_color, start_btn, 3)
                # change menu flag
                self.menu_showed = True
                
            # check if "Settings" button was clicked
            elif settings_btn.collidepoint(mouse_coords[0], mouse_coords[1]):
                # Ouvrir le menu de paramètres
                settings_menu = SettingsMenu(self.screen)
                result = settings_menu.run()
                
                # Recharger les paramètres après fermeture du menu
                if result == "save":
                    self.stockfish_settings.load_settings()
                    print("Nouveaux paramètres Stockfish :")
                    print(f"  - ELO: {self.stockfish_settings.get_elo()}")
                    print(f"  - Skill Level: {self.stockfish_settings.settings['skill_level']}")
                    print(f"  - Temps: {self.stockfish_settings.settings['time_limit']}s")
                
            # check if enter or return key was pressed
            elif key_pressed[K_RETURN]:
                self.menu_showed = True


    def game(self):
        # background color
        color = (0,0,0)
        # set backgound color
        self.screen.fill(color)
        
        # show the chess board
        self.screen.blit(self.board_img, self.board_dimensions)

        # Afficher un message si Stockfish réfléchit
        if self.chess.stockfish_thinking:
            white_color = (255, 255, 255)
            small_font = pygame.font.SysFont("comicsansms", 20)
            thinking_text = small_font.render("Stockfish is thinking...", True, white_color)
            self.screen.blit(thinking_text, 
                          ((self.screen.get_width() - thinking_text.get_width()) // 2,
                          30))

        # call chess play turn method
        self.chess.play_turn()
        # draw pieces on the chess board
        self.chess.draw_pieces()


    def declare_winner(self, winner):
        # background color
        bg_color = (255, 255, 255)
        # set background color
        self.screen.fill(bg_color)
        # black color
        black_color = (0, 0, 0)
        # coordinates for play again button
        reset_btn = pygame.Rect(180, 300, 140, 50)
        menu_btn = pygame.Rect(330, 300, 140, 50)
        
        # show buttons
        pygame.draw.rect(self.screen, black_color, reset_btn)
        pygame.draw.rect(self.screen, (50, 100, 200), menu_btn)

        # white color
        white_color = (255, 255, 255)
        # create fonts for texts
        big_font = pygame.font.SysFont("comicsansms", 50)
        small_font = pygame.font.SysFont("comicsansms", 20)

        # text to show winner
        if winner == "White":
            text = "You win!"
        else:
            text = "Stockfish wins!"
            
        winner_text = big_font.render(text, False, black_color)

        # create text to be shown on buttons
        reset_label = "Play Again"
        menu_label = "Menu"
        reset_btn_label = small_font.render(reset_label, True, white_color)
        menu_btn_label = small_font.render(menu_label, True, white_color)

        # show winner text
        self.screen.blit(winner_text, 
                      ((self.screen.get_width() - winner_text.get_width()) // 2, 
                      150))
        
        # show text on buttons
        self.screen.blit(reset_btn_label, 
                      ((reset_btn.x + (reset_btn.width - reset_btn_label.get_width()) // 2, 
                      reset_btn.y + (reset_btn.height - reset_btn_label.get_height()) // 2)))
        
        self.screen.blit(menu_btn_label, 
                      ((menu_btn.x + (menu_btn.width - menu_btn_label.get_width()) // 2, 
                      menu_btn.y + (menu_btn.height - menu_btn_label.get_height()) // 2)))

        # get pressed keys
        key_pressed = pygame.key.get_pressed()
        # 
        util = Utils()

        # check if left mouse button was clicked
        if util.left_click_event():
            # call function to get mouse event
            mouse_coords = util.get_mouse_event()

            # check if reset button was clicked
            if reset_btn.collidepoint(mouse_coords[0], mouse_coords[1]):
                # change button behavior as it is hovered
                pygame.draw.rect(self.screen, white_color, reset_btn, 3)
                
                # reset game
                self.chess.reset()
                # clear winner
                self.chess.winner = ""
                
            # check if menu button was clicked
            elif menu_btn.collidepoint(mouse_coords[0], mouse_coords[1]):
                # change menu flag
                self.menu_showed = False
                # reset game
                self.chess.reset()
                # clear winner
                self.chess.winner = ""
                
            # check if enter or return key was pressed
            elif key_pressed[K_RETURN]:
                self.menu_showed = False
                # reset game
                self.chess.reset()
                # clear winner
                self.chess.winner = ""