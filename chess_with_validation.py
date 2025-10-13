import pygame
from pygame.locals import *
import random
import time
import chess  # Pour valider les coups

from piece import Piece
from utils import Utils

class Chess(object):
    def __init__(self, screen, pieces_src, square_coords, square_length):
        # display surface
        self.screen = screen
        # create an object of class to show chess pieces on the board
        self.chess_pieces = Piece(pieces_src, cols=6, rows=2)
        # store coordinates of the chess board squares
        self.board_locations = square_coords
        # length of the side of a chess board square
        self.square_length = square_length
        # dictionary to keeping track of player turn
        self.turn = {"black": 0,
                     "white": 0}

        # list containing possible moves for the selected piece
        self.moves = []
        #
        self.utils = Utils()

        # Stockfish configuration
        self.ENGINE_SCRIPT = "uci_stockfish.py"
        self.BESTMOVE_FILE = "bestmove.txt"
        self.stockfish_thinking = False
        self.stockfish_failures = 0

        # Instance persistante du moteur universel
        self.engine_instance = None
        self.initialize_engine()

        # Board de validation avec python-chess
        self.validation_board = chess.Board()

        # mapping of piece names to index of list containing piece coordinates on spritesheet
        self.pieces = {
            "white_pawn":   5,
            "white_knight": 3,
            "white_bishop": 2,
            "white_rook":   4,
            "white_king":   0,
            "white_queen":  1,
            "black_pawn":   11,
            "black_knight": 9,
            "black_bishop": 8,
            "black_rook":   10,
            "black_king":   6,
            "black_queen":  7
        }

        # list containing captured pieces
        self.captured = []
        #
        self.winner = ""

        self.reset()

    def initialize_engine(self):
        """Initialise le moteur d'échecs une seule fois au début"""
        try:
            from universal_engine import get_universal_engine
            self.engine_instance = get_universal_engine()
            if self.engine_instance.initialize():
                print("Moteur d'échecs initialisé avec succès!")
                return True
            else:
                print("Échec de l'initialisation du moteur")
                self.engine_instance = None
                return False
        except Exception as e:
            print(f"Erreur lors de l'initialisation du moteur: {e}")
            self.engine_instance = None
            return False

    def reset(self):
        # clear moves lists
        self.moves = []
        self.stockfish_thinking = False
        self.stockfish_failures = 0
        
        # Réinitialiser le board de validation
        self.validation_board = chess.Board()

        # Le joueur humain joue toujours les blancs (commence)
        self.turn["black"] = 0
        self.turn["white"] = 1

        # two dimensonal dictionary containing details about each board location
        # storage format is [piece_name, currently_selected, x_y_coordinate]
        self.piece_location = {}
        x = 0
        for i in range(97, 105):
            a = 8
            y = 0
            self.piece_location[chr(i)] = {}
            while a>0:
                # [piece name, currently selected, board coordinates]
                self.piece_location[chr(i)][a] = ["", False, [x,y]]
                a = a - 1
                y = y + 1
            x = x + 1

        # reset the board
        for i in range(97, 105):
            x = 8
            while x>0:
                if(x==8):
                    if(chr(i)=='a' or chr(i)=='h'):
                        self.piece_location[chr(i)][x][0] = "black_rook"
                    elif(chr(i)=='b' or chr(i)=='g'):
                        self.piece_location[chr(i)][x][0] = "black_knight"
                    elif(chr(i)=='c' or chr(i)=='f'):
                        self.piece_location[chr(i)][x][0] = "black_bishop"
                    elif(chr(i)=='d'):
                        self.piece_location[chr(i)][x][0] = "black_queen"
                    elif(chr(i)=='e'):
                        self.piece_location[chr(i)][x][0] = "black_king"
                elif(x==7):
                    self.piece_location[chr(i)][x][0] = "black_pawn"
                elif(x==2):
                    self.piece_location[chr(i)][x][0] = "white_pawn"
                elif(x==1):
                    if(chr(i)=='a' or chr(i)=='h'):
                        self.piece_location[chr(i)][x][0] = "white_rook"
                    elif(chr(i)=='b' or chr(i)=='g'):
                        self.piece_location[chr(i)][x][0] = "white_knight"
                    elif(chr(i)=='c' or chr(i)=='f'):
                        self.piece_location[chr(i)][x][0] = "white_bishop"
                    elif(chr(i)=='d'):
                        self.piece_location[chr(i)][x][0] = "white_queen"
                    elif(chr(i)=='e'):
                        self.piece_location[chr(i)][x][0] = "white_king"
                x = x - 1

    def get_fen(self):
        """Utilise le board de validation pour obtenir une FEN correcte"""
        try:
            return self.validation_board.fen()
        except Exception as e:
            print(f"Erreur lors de l'obtention de la FEN: {e}")
            # Retourner une position de départ par défaut
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def sync_validation_board(self):
        """Synchronise le board de validation avec la position interne"""
        try:
            # Créer une position vide
            board_fen = ""
            
            # Parcourir le plateau de haut en bas (rank 8 à 1)
            for rank in range(8, 0, -1):
                empty_count = 0
                for file_char in "abcdefgh":
                    piece = self.piece_location[file_char][rank][0]
                    
                    if piece == "":
                        empty_count += 1
                    else:
                        if empty_count > 0:
                            board_fen += str(empty_count)
                            empty_count = 0
                        
                        # Convertir le nom de pièce en notation FEN
                        if piece.startswith("white"):
                            if piece.endswith("pawn"):
                                board_fen += "P"
                            elif piece.endswith("rook"):
                                board_fen += "R"
                            elif piece.endswith("knight"):
                                board_fen += "N"
                            elif piece.endswith("bishop"):
                                board_fen += "B"
                            elif piece.endswith("queen"):
                                board_fen += "Q"
                            elif piece.endswith("king"):
                                board_fen += "K"
                        else:  # black pieces
                            if piece.endswith("pawn"):
                                board_fen += "p"
                            elif piece.endswith("rook"):
                                board_fen += "r"
                            elif piece.endswith("knight"):
                                board_fen += "n"
                            elif piece.endswith("bishop"):
                                board_fen += "b"
                            elif piece.endswith("queen"):
                                board_fen += "q"
                            elif piece.endswith("king"):
                                board_fen += "k"
                
                if empty_count > 0:
                    board_fen += str(empty_count)
                
                if rank > 1:
                    board_fen += "/"
            
            # Ajouter les autres parties de la FEN
            turn = "w" if self.turn["white"] else "b"
            castling = "KQkq"  # Simplifié
            en_passant = "-"   # Simplifié
            halfmove = "0"     # Simplifié
            fullmove = str(self.validation_board.fullmove_number)
            
            fen = f"{board_fen} {turn} {castling} {en_passant} {halfmove} {fullmove}"
            
            # Essayer de créer un board avec cette FEN
            self.validation_board = chess.Board(fen)
            return True
            
        except Exception as e:
            print(f"Erreur lors de la synchronisation: {e}")
            # En cas d'erreur, garder l'ancien board
            return False

    def validate_and_apply_human_move(self, move_uci, from_file, from_rank, to_file, to_rank, piece_name):
        """Valide et applique un coup humain en synchronisant avec le board de validation"""
        try:
            # D'abord synchroniser le board de validation avec la position actuelle
            if not self.sync_validation_board():
                print("Erreur: Impossible de synchroniser le board de validation")
                return False
            
            # Vérifier que le coup est légal avec python-chess
            try:
                move = chess.Move.from_uci(move_uci)
                if move not in self.validation_board.legal_moves:
                    print(f"Coup humain illégal: {move_uci}")
                    return False
            except Exception as e:
                print(f"Erreur dans le format du coup humain: {move_uci} - {e}")
                return False
            
            # Le coup est légal, on peut l'appliquer
            
            # 1. Appliquer sur le board de validation
            self.validation_board.push(move)
            
            # 2. Appliquer sur la représentation interne
            target_piece = self.piece_location[to_file][to_rank][0]
            
            # Gérer les captures (pour l'affichage seulement)
            if target_piece != "":
                self.captured.append(self.piece_location[to_file][to_rank].copy())
            
            # Déplacer la pièce
            self.piece_location[to_file][to_rank][0] = piece_name
            self.piece_location[from_file][from_rank][0] = ""
            
            # 3. Changer de tour
            if self.turn["white"]:
                self.turn["white"] = 0
                self.turn["black"] = 1
            else:
                self.turn["black"] = 0
                self.turn["white"] = 1
            
            # 4. Vérifier l'état du jeu après le coup
            self.check_game_status()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la validation du coup humain: {e}")
            return False

    def validate_and_apply_move(self, move_uci):
        """Valide et applique un coup en utilisant python-chess"""
        try:
            print(f"DEBUG: Tentative d'application du coup {move_uci}")

            # Forcer la synchronisation avant de valider
            print("DEBUG: Synchronisation du board de validation...")
            self.sync_validation_board()

            # Le board de validation devrait déjà être synchronisé, mais on vérifie
            current_fen = self.validation_board.fen()
            print(f"Board de validation avant coup Stockfish: {current_fen}")

            # Créer le coup
            move = chess.Move.from_uci(move_uci)
            print(f"DEBUG: Coup UCI parsé: {move}")

            # Vérifier que le coup est légal
            if move not in self.validation_board.legal_moves:
                print(f"ERREUR: Coup illégal détecté: {move_uci}")
                print(f"Position actuelle: {self.validation_board.fen()}")
                legal_moves_list = [m.uci() for m in self.validation_board.legal_moves]
                print(f"Coups légaux: {legal_moves_list[:10]}...")  # Afficher les 10 premiers

                # Debug supplémentaire: vérifier si c'est un problème de tour
                if self.validation_board.turn:
                    print("DEBUG: C'est au tour des BLANCS de jouer")
                else:
                    print("DEBUG: C'est au tour des NOIRS de jouer")

                return False

            print(f"DEBUG: Coup légal, application...")

            # Appliquer le coup sur le board de validation
            self.validation_board.push(move)

            # Appliquer le coup sur notre représentation interne
            result = self.apply_move_to_internal_board(move_uci)
            print(f"DEBUG: Résultat application interne: {result}")
            return result

        except Exception as e:
            print(f"ERREUR lors de la validation du coup {move_uci}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def apply_move_to_internal_board(self, move_uci):
        """Applique un coup validé sur notre représentation interne"""
        if len(move_uci) < 4:
            return False
        
        from_square = move_uci[:2]
        to_square = move_uci[2:4]
        
        from_file = from_square[0]
        from_rank = int(from_square[1])
        to_file = to_square[0]
        to_rank = int(to_square[1])
        
        # Vérifier que les coordonnées sont valides
        if (from_file < 'a' or from_file > 'h' or 
            to_file < 'a' or to_file > 'h' or
            from_rank < 1 or from_rank > 8 or
            to_rank < 1 or to_rank > 8):
            return False
        
        # Obtenir la pièce à déplacer
        source_piece = self.piece_location[from_file][from_rank][0]
        target_piece = self.piece_location[to_file][to_rank][0]
        
        if source_piece == "":
            print(f"Erreur: Aucune pièce à déplacer en {from_square}")
            return False
        
        # Vérifier si c'est une capture (pour l'affichage seulement)
        if target_piece != "":
            # Ajouter la pièce capturée à la liste pour l'affichage
            self.captured.append(self.piece_location[to_file][to_rank].copy())
        
        # Effectuer le déplacement
        self.piece_location[to_file][to_rank][0] = source_piece
        self.piece_location[from_file][from_rank][0] = ""
        
        # Changer de tour
        if self.turn["black"]:
            self.turn["black"] = 0
            self.turn["white"] = 1
        else:
            self.turn["black"] = 1
            self.turn["white"] = 0
        
        # Vérifier l'état du jeu après le coup
        self.check_game_status()
        
        print(f"Coup appliqué: {move_uci} ({source_piece} de {from_square} vers {to_square})")
        return True

    def check_game_status(self):
        """Vérifie l'état du jeu (échec, mat, pat, etc.)"""
        try:
            status_messages = []
            
            # Vérifier les différents états
            if self.validation_board.is_checkmate():
                if self.validation_board.turn == chess.WHITE:
                    self.winner = "Black"
                    status_messages.append("ÉCHEC ET MAT ! Les noirs gagnent !")
                else:
                    self.winner = "White"  
                    status_messages.append("ÉCHEC ET MAT ! Les blancs gagnent !")
                    
            elif self.validation_board.is_stalemate():
                self.winner = "Draw"
                status_messages.append("PAT ! Match nul !")
                
            elif self.validation_board.is_insufficient_material():
                self.winner = "Draw"
                status_messages.append("MATÉRIEL INSUFFISANT ! Match nul !")
                
            elif self.validation_board.can_claim_threefold_repetition():
                self.winner = "Draw"
                status_messages.append("RÉPÉTITION DE POSITION ! Match nul possible !")
                
            elif self.validation_board.can_claim_fifty_moves():
                self.winner = "Draw"
                status_messages.append("RÈGLE DES 50 COUPS ! Match nul possible !")
                
            elif self.validation_board.is_check():
                if self.validation_board.turn == chess.WHITE:
                    status_messages.append("ÉCHEC aux blancs !")
                else:
                    status_messages.append("ÉCHEC aux noirs !")
            
            # Afficher les messages de statut
            for msg in status_messages:
                print(f">>> {msg}")
                
            return len(status_messages) > 0
            
        except Exception as e:
            print(f"Erreur lors de la vérification du statut: {e}")
            return False

    def get_game_result_text(self):
        """Retourne le texte du résultat pour l'affichage"""
        if self.winner == "White":
            return "You Win! (Checkmate)"
        elif self.winner == "Black": 
            return "Stockfish Wins! (Checkmate)"
        elif self.winner == "Draw":
            return "Draw! (Stalemate/Rule)"
        else:
            return "Game in Progress"
        

    def run_stockfish_move(self):
        """Lance Stockfish pour obtenir le meilleur coup"""
        if self.stockfish_thinking:
            return

        self.stockfish_thinking = True
        fen = self.get_fen()  # Utilise directement le board de validation

        print(f"Position FEN: {fen}")

        try:
            # Utiliser l'instance persistante du moteur
            if self.engine_instance is None:
                print("Moteur non initialisé, tentative de réinitialisation...")
                if not self.initialize_engine():
                    print("Impossible d'initialiser le moteur, passage en mode aléatoire")
                    self.stockfish_failures += 1
                    if self.stockfish_failures >= 3:
                        self.play_random_move()
                    else:
                        self.turn["black"] = 0
                        self.turn["white"] = 1
                    self.stockfish_thinking = False
                    return

            # Obtenir le meilleur coup directement depuis l'instance du moteur
            bestmove = self.engine_instance.get_best_move(fen)

            if bestmove and len(bestmove) >= 4:
                # Valider et appliquer le coup (le board de validation est déjà synchronisé)
                if self.validate_and_apply_move(bestmove):
                    print(f"Stockfish joue: {bestmove}")
                    self.stockfish_failures = 0  # Réinitialiser le compteur
                else:
                    print(f"Coup Stockfish rejeté: {bestmove}")
                    self.stockfish_failures += 1
                    if self.stockfish_failures >= 3:
                        print("Trop d'échecs, passage en mode aléatoire")
                        self.play_random_move()
                    else:
                        # Changer de tour pour continuer
                        self.turn["black"] = 0
                        self.turn["white"] = 1
            else:
                print(f"Coup invalide ou moteur n'a pas trouvé de coup")
                self.stockfish_failures += 1
                if self.stockfish_failures >= 3:
                    print("Trop d'échecs de Stockfish, passage en mode coup aléatoire")
                    self.play_random_move()
                else:
                    print("Stockfish indisponible, tour passé")
                    # Changer de tour pour continuer le jeu
                    self.turn["black"] = 0
                    self.turn["white"] = 1

        except Exception as e:
            print(f"Erreur inattendue: {e}")
            import traceback
            traceback.print_exc()
            self.stockfish_failures += 1
            if self.stockfish_failures >= 3:
                print("Passage en mode aléatoire après erreur")
                self.play_random_move()
            else:
                self.turn["black"] = 0
                self.turn["white"] = 1

        self.stockfish_thinking = False

    def play_random_move(self):
        """Joue un coup aléatoire valide pour les noirs"""
        try:
            # Le board de validation devrait déjà être synchronisé
            print(f"Position pour coup aléatoire: {self.validation_board.fen()}")
            
            # Obtenir tous les coups légaux
            legal_moves = []
            for move in self.validation_board.legal_moves:
                legal_moves.append(move.uci())
            
            if legal_moves:
                # Choisir un coup aléatoire
                random_move = random.choice(legal_moves)
                print(f"Coup aléatoire choisi parmi {len(legal_moves)} options: {random_move}")
                
                if self.validate_and_apply_move(random_move):
                    print(f"IA joue (aléatoire): {random_move}")
                else:
                    print("Échec du coup aléatoire, tour passé")
                    self.turn["black"] = 0
                    self.turn["white"] = 1
            else:
                print("Aucun coup légal disponible")
                self.turn["black"] = 0
                self.turn["white"] = 1
                
        except Exception as e:
            print(f"Erreur dans coup aléatoire: {e}")
            self.turn["black"] = 0
            self.turn["white"] = 1

    def play_turn(self):
        # white color
        white_color = (255, 255, 255)
        red_color = (255, 100, 100)
        # create fonts for texts
        small_font = pygame.font.SysFont("comicsansms", 20)
        
        # create text to be shown on the game menu
        if self.turn["black"]:
            if self.stockfish_failures >= 3:
                turn_text = small_font.render("Turn: Black (Random AI)", True, white_color)
            else:
                turn_text = small_font.render("Turn: Black (Stockfish)", True, white_color)
        elif self.turn["white"]:
            turn_text = small_font.render("Turn: White (Human)", True, white_color)
        
        # show turn text
        self.screen.blit(turn_text, 
                      ((self.screen.get_width() - turn_text.get_width()) // 2,
                      10))
        
        # Afficher le statut du jeu (échec, mat, etc.)
        try:
            if self.validation_board.is_check() and not self.validation_board.is_game_over():
                if self.validation_board.turn == chess.WHITE:
                    check_text = small_font.render("CHECK - White in check!", True, red_color)
                else:
                    check_text = small_font.render("CHECK - Black in check!", True, red_color)
                
                self.screen.blit(check_text, 
                              ((self.screen.get_width() - check_text.get_width()) // 2, 30))
                              
        except Exception as e:
            # Ignorer les erreurs de validation board pendant l'affichage
            pass
        
        # Si c'est le tour de Stockfish et qu'il ne réfléchit pas déjà
        if self.turn["black"] and not self.stockfish_thinking and self.winner == "":
            # Lancer Stockfish après un petit délai
            pygame.time.wait(500)
            self.run_stockfish_move()
        
        # let player with white piece play (human)
        elif self.turn["white"] and self.winner == "":
            self.move_piece("white")

    # method to draw pieces on the chess board
    def draw_pieces(self):
        transparent_green = (0,194,39,170)
        transparent_blue = (28,21,212,170)

        # create a transparent surface
        surface = pygame.Surface((self.square_length, self.square_length), pygame.SRCALPHA)
        surface.fill(transparent_green)

        surface1 = pygame.Surface((self.square_length, self.square_length), pygame.SRCALPHA)
        surface1.fill(transparent_blue)

        # loop to change background color of selected piece
        for val in self.piece_location.values():
            for value in val.values() :
                # name of the piece in the current location
                piece_name = value[0]
                # x, y coordinates of the current piece
                piece_coord_x, piece_coord_y = value[2]

                # change background color of piece if it is selected
                if value[1] and len(value[0]) > 5:
                    # if the piece selected is a black piece
                    if value[0][:5] == "black":
                        self.screen.blit(surface, self.board_locations[piece_coord_x][piece_coord_y])
                        if len(self.moves) > 0:
                            for move in self.moves:
                                x_coord = move[0]
                                y_coord = move[1]
                                if x_coord >= 0 and y_coord >= 0 and x_coord < 8 and y_coord < 8:
                                    self.screen.blit(surface, self.board_locations[x_coord][y_coord])
                    # if the piece selected is a white piece
                    elif value[0][:5] == "white":
                        self.screen.blit(surface1, self.board_locations[piece_coord_x][piece_coord_y])
                        if len(self.moves) > 0:
                            for move in self.moves:
                                x_coord = move[0]
                                y_coord = move[1]
                                if x_coord >= 0 and y_coord >= 0 and x_coord < 8 and y_coord < 8:
                                    self.screen.blit(surface1, self.board_locations[x_coord][y_coord])
        
        # draw all chess pieces
        for val in self.piece_location.values():
            for value in val.values() :
                # name of the piece in the current location
                piece_name = value[0]
                # x, y coordinates of the current piece
                piece_coord_x, piece_coord_y = value[2]
                # check if there is a piece at the square
                if(len(value[0]) > 1):
                    # draw piece on the board
                    self.chess_pieces.draw(self.screen, piece_name, 
                                            self.board_locations[piece_coord_x][piece_coord_y])

    # method to find the possible moves of the selected piece
    def possible_moves(self, piece_name, piece_coord):
        # list to store possible moves of the selected piece
        positions = []
        # find the possible locations to put a piece
        if len(piece_name) > 0:
            # get x, y coordinate
            x_coord, y_coord = piece_coord
            # calculate moves for bishop
            if piece_name[6:] == "bishop":
                positions = self.diagonal_moves(positions, piece_name, piece_coord)
            
            # calculate moves for pawn
            elif piece_name[6:] == "pawn":
                # convert list index to dictionary key
                columnChar = chr(97 + x_coord)
                rowNo = 8 - y_coord

                # calculate moves for white pawn
                if piece_name == "black_pawn":
                    if y_coord + 1 < 8:
                        # get row in front of black pawn
                        rowNo = rowNo - 1
                        front_piece = self.piece_location[columnChar][rowNo][0]
                
                        # pawns cannot move when blocked by another another pawn
                        if(front_piece[6:] != "pawn"):
                            positions.append([x_coord, y_coord+1])
                            # black pawns can move two positions ahead for first move
                            if y_coord < 2:
                                positions.append([x_coord, y_coord+2])

                        # EM PASSANT
                        # diagonal to the left
                        if x_coord - 1 >= 0 and y_coord + 1 < 8:
                            x = x_coord - 1
                            y = y_coord + 1
                            
                            # convert list index to dictionary key
                            columnChar = chr(97 + x)
                            rowNo = 8 - y
                            to_capture = self.piece_location[columnChar][rowNo]

                            if(to_capture[0][:5] == "white"):
                                positions.append([x, y])
                        
                        # diagonal to the right
                        if x_coord + 1 < 8  and y_coord + 1 < 8:
                            x = x_coord + 1
                            y = y_coord + 1

                            # convert list index to dictionary key
                            columnChar = chr(97 + x)
                            rowNo = 8 - y
                            to_capture = self.piece_location[columnChar][rowNo]

                            if(to_capture[0][:5] == "white"):
                                positions.append([x, y])
                        
                # calculate moves for white pawn
                elif piece_name == "white_pawn":
                    if y_coord - 1 >= 0:
                        # get row in front of black pawn
                        rowNo = rowNo + 1
                        front_piece = self.piece_location[columnChar][rowNo][0]

                        # pawns cannot move when blocked by another another pawn
                        if(front_piece[6:] != "pawn"):
                            positions.append([x_coord, y_coord-1])
                            # black pawns can move two positions ahead for first move
                            if y_coord > 5:
                                positions.append([x_coord, y_coord-2])

                        # EM PASSANT
                        # diagonal to the left
                        if x_coord - 1 >= 0 and y_coord - 1 >= 0:
                            x = x_coord - 1
                            y = y_coord - 1
                            
                            # convert list index to dictionary key
                            columnChar = chr(97 + x)
                            rowNo = 8 - y
                            to_capture = self.piece_location[columnChar][rowNo]

                            if(to_capture[0][:5] == "black"):
                                positions.append([x, y])

                            
                        # diagonal to the right
                        if x_coord + 1 < 8  and y_coord - 1 >= 0:
                            x = x_coord + 1
                            y = y_coord - 1

                            # convert list index to dictionary key
                            columnChar = chr(97 + x)
                            rowNo = 8 - y
                            to_capture = self.piece_location[columnChar][rowNo]

                            if(to_capture[0][:5] == "black"):
                                positions.append([x, y])


            # calculate moves for rook
            elif piece_name[6:] == "rook":
                # find linear moves
                positions = self.linear_moves(positions, piece_name, piece_coord)

            # calculate moves for knight
            elif piece_name[6:] == "knight":
                # left positions
                if(x_coord - 2) >= 0:
                    if(y_coord - 1) >= 0:
                        positions.append([x_coord-2, y_coord-1])
                    if(y_coord + 1) < 8:
                        positions.append([x_coord-2, y_coord+1])
                # top positions
                if(y_coord - 2) >= 0:
                    if(x_coord - 1) >= 0:
                        positions.append([x_coord-1, y_coord-2])
                    if(x_coord + 1) < 8:
                        positions.append([x_coord+1, y_coord-2])
                # right positions
                if(x_coord + 2) < 8:
                    if(y_coord - 1) >= 0:
                        positions.append([x_coord+2, y_coord-1])
                    if(y_coord + 1) < 8:
                        positions.append([x_coord+2, y_coord+1])
                # bottom positions
                if(y_coord + 2) < 8:
                    if(x_coord - 1) >= 0:
                        positions.append([x_coord-1, y_coord+2])
                    if(x_coord + 1) < 8:
                        positions.append([x_coord+1, y_coord+2])

            # calculate movs for king
            elif piece_name[6:] == "king":
                if(y_coord - 1) >= 0:
                    # top spot
                    positions.append([x_coord, y_coord-1])

                if(y_coord + 1) < 8:
                    # bottom spot
                    positions.append([x_coord, y_coord+1])

                if(x_coord - 1) >= 0:
                    # left spot
                    positions.append([x_coord-1, y_coord])
                    # top left spot
                    if(y_coord - 1) >= 0:
                        positions.append([x_coord-1, y_coord-1])
                    # bottom left spot
                    if(y_coord + 1) < 8:
                        positions.append([x_coord-1, y_coord+1])
                    
                if(x_coord + 1) < 8:
                    # right spot
                    positions.append([x_coord+1, y_coord])
                    # top right spot
                    if(y_coord - 1) >= 0:
                        positions.append([x_coord+1, y_coord-1])
                    # bottom right spot
                    if(y_coord + 1) < 8:
                        positions.append([x_coord+1, y_coord+1])
                
            # calculate movs for queen
            elif piece_name[6:] == "queen":
                # find diagonal positions
                positions = self.diagonal_moves(positions, piece_name, piece_coord)

                # find linear moves
                positions = self.linear_moves(positions, piece_name, piece_coord)

            # list of positions to be removed
            to_remove = []

            # remove positions that overlap other pieces of the current player
            for pos in positions:
                x, y = pos

                # convert list index to dictionary key
                columnChar = chr(97 + x)
                rowNo = 8 - y

                # find the pieces to remove
                des_piece_name = self.piece_location[columnChar][rowNo][0]
                if(des_piece_name[:5] == piece_name[:5]):
                    to_remove.append(pos)

            # remove position from positions list
            for i in to_remove:
                positions.remove(i)

        # return list containing possible moves for the selected piece
        return positions


    def move_piece(self, turn):
        # get the coordinates of the square selected on the board
        square = self.get_selected_square()

        # if a square was selected
        if square:
            # get name of piece on the selected square
            piece_name = square[0]
            # color of piece on the selected square
            piece_color = piece_name[:5]
            # board column character
            columnChar = square[1]
            # board row number
            rowNo = square[2]

            # get x, y coordinates
            x, y = self.piece_location[columnChar][rowNo][2]

            # if there's a piece on the selected square
            if(len(piece_name) > 0) and (piece_color == turn):
                # find possible moves for thr piece
                self.moves = self.possible_moves(piece_name, [x,y])

            # checkmate mechanism
            p = self.piece_location[columnChar][rowNo]

            for i in self.moves:
                if i == [x, y]:
                    if(p[0][:5] == turn) or len(p[0]) == 0:
                        self.validate_move([x,y])
                    else:
                        self.capture_piece(turn, [columnChar, rowNo], [x,y])

            # only the player with the turn gets to play
            if(piece_color == turn):
                # change selection flag from all other pieces
                for k in self.piece_location.keys():
                    for key in self.piece_location[k].keys():
                        self.piece_location[k][key][1] = False

                # change selection flag of the selected piece
                self.piece_location[columnChar][rowNo][1] = True
                
            
    def get_selected_square(self):
        # get left event
        left_click = self.utils.left_click_event()

        # if there's a mouse event
        if left_click:
            # get mouse event
            mouse_event = self.utils.get_mouse_event()

            for i in range(len(self.board_locations)):
                for j in range(len(self.board_locations)):
                    rect = pygame.Rect(self.board_locations[i][j][0], self.board_locations[i][j][1], 
                            self.square_length, self.square_length)
                    collision = rect.collidepoint(mouse_event[0], mouse_event[1])
                    if collision:
                        selected = [rect.x, rect.y]
                        # find x, y coordinates the selected square
                        for k in range(len(self.board_locations)):
                            #
                            try:
                                l = None
                                l = self.board_locations[k].index(selected)
                                if l != None:
                                    #reset color of all selected pieces
                                    for val in self.piece_location.values():
                                        for value in val.values() :
                                            # [piece name, currently selected, board coordinates]
                                            if not value[1]:
                                                value[1] = False

                                    # get column character and row number of the chess piece
                                    columnChar = chr(97 + k)
                                    rowNo = 8 - l
                                    # get the name of the 
                                    piece_name = self.piece_location[columnChar][rowNo][0]
                                    
                                    return [piece_name, columnChar, rowNo]
                            except:
                                pass
        else:
            return None


    def capture_piece(self, turn, chess_board_coord, piece_coord):
        # Cette méthode utilise maintenant le système de validation approprié
        # qui gère correctement les règles d'échec et mat
        self.validate_move(piece_coord)


    def validate_move(self, destination):
        desColChar = chr(97 + destination[0])
        desRowNo = 8 - destination[1]

        for k in self.piece_location.keys():
            for key in self.piece_location[k].keys():
                board_piece = self.piece_location[k][key]

                if board_piece[1]:
                    # unselect the source piece
                    self.piece_location[k][key][1] = False
                    # get the name of the source piece
                    piece_name = self.piece_location[k][key][0]
                    
                    # Créer le coup UCI pour validation
                    move_uci = f"{k}{key}{desColChar}{desRowNo}".lower()
                    
                    # Valider le coup humain avec le système de validation
                    if self.validate_and_apply_human_move(move_uci, k, key, desColChar, desRowNo, piece_name):
                        src_location = k + str(key)
                        des_location = desColChar + str(desRowNo)
                        print("{} moved from {} to {}".format(piece_name, src_location, des_location))
                    break


    # helper function to find diagonal moves
    def diagonal_moves(self, positions, piece_name, piece_coord):
        # reset x and y coordinate values
        x, y = piece_coord
        # find top left diagonal spots
        while(True):
            x = x - 1
            y = y - 1
            if(x < 0 or y < 0):
                break
            else:
                positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break

        # reset x and y coordinate values
        x, y = piece_coord
        # find bottom right diagonal spots
        while(True):
            x = x + 1
            y = y + 1
            if(x > 7 or y > 7):
                break
            else:
                positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break

        # reset x and y coordinate values
        x, y = piece_coord
        # find bottom left diagonal spots
        while(True):
            x = x - 1
            y = y + 1
            if (x < 0 or y > 7):
                break
            else:
                positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break

        # reset x and y coordinate values
        x, y = piece_coord
        # find top right diagonal spots
        while(True):
            x = x + 1
            y = y - 1
            if(x > 7 or y < 0):
                break
            else:
                positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break

        return positions
    

    # helper function to find horizontal and vertical moves
    def linear_moves(self, positions, piece_name, piece_coord):
        # reset x, y coordniate value
        x, y = piece_coord
        # horizontal moves to the left
        while(x > 0):
            x = x - 1
            positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break
                    

        # reset x, y coordniate value
        x, y = piece_coord
        # horizontal moves to the right
        while(x < 7):
            x = x + 1
            positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break    

        # reset x, y coordniate value
        x, y = piece_coord
        # vertical moves upwards
        while(y > 0):
            y = y - 1
            positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break

        # reset x, y coordniate value
        x, y = piece_coord
        # vertical moves downwards
        while(y < 7):
            y = y + 1
            positions.append([x,y])

            # convert list index to dictionary key
            columnChar = chr(97 + x)
            rowNo = 8 - y
            p = self.piece_location[columnChar][rowNo]

            # stop finding possible moves if blocked by a piece
            if len(p[0]) > 0 and piece_name[:5] != p[0][:5]:
                break


        return positions