import pygame
from pygame.locals import *
import random
import time
import chess

from piece import Piece
from utils import Utils

class Chess(object):
    # MODIFIED: Constructor now accepts player_color for PVP setup and robot_wait_callback
    def __init__(self, screen, pieces_src, square_coords, square_length, mode, player_color='WHITE', robot_wait_callback=None):
        self.screen = screen
        self.mode = mode
        self.player_color = player_color # Store the color this instance plays as
        self.chess_pieces = Piece(pieces_src, cols=6, rows=2)
        self.board_locations = square_coords
        self.square_length = square_length
        self.turn = {"black": 0, "white": 1}
        self.robot_wait_callback = robot_wait_callback  # Callback pour attendre le robot

        self.moves = []
        self.utils = Utils()
        self.BESTMOVE_FILE = "next_move.txt"
        self.stockfish_thinking = False
        self.stockfish_failures = 0
        self.engine_instance = None
        
        if self.mode == 'pve':
            self.initialize_engine()

        self.validation_board = chess.Board()
        self.pieces = {
            "white_pawn": 5, "white_knight": 3, "white_bishop": 2, "white_rook": 4, "white_king": 0, "white_queen": 1,
            "black_pawn": 11, "black_knight": 9, "black_bishop": 8, "black_rook": 10, "black_king": 6, "black_queen": 7
        }
        self.winner = ""
        self.white_captured = []  # Pièces noires capturées par les blancs
        self.black_captured = []  # Pièces blanches capturées par les noirs
        self.reset()

    def get_winner(self):
        """Simple getter for the winner status."""
        return self.winner if self.winner in ["White", "Black", "Draw"] else None

    def initialize_engine(self):
        """Initialises the chess engine for PVE mode."""
        try:
            from universal_engine import get_universal_engine
            self.engine_instance = get_universal_engine()
            if self.engine_instance.initialize():
                print("Chess engine initialized successfully!")
            else:
                self.engine_instance = None
        except Exception as e:
            print(f"Error initializing engine: {e}")
            self.engine_instance = None

    def reset(self):
        """Resets the game to the starting position."""
        self.moves = []
        self.stockfish_thinking = False
        self.winner = ""
        self.validation_board = chess.Board()
        self.turn = {"black": 0, "white": 1}
        self.white_captured = []
        self.black_captured = []

        self.piece_location = {chr(i): {j: ["", False, [k, 8-j]] for j in range(1, 9)} for k, i in enumerate(range(97, 105))}
        setup = {
            1: ["white_pawn", "white_rook", "white_knight", "white_bishop", "white_queen", "white_king"],
            2: ["white_pawn"], 7: ["black_pawn"],
            8: ["black_pawn", "black_rook", "black_knight", "black_bishop", "black_queen", "black_king"]
        }
        for rank, pieces in setup.items():
            if len(pieces) > 1:
                self.piece_location['a'][rank][0], self.piece_location['h'][rank][0] = pieces[1], pieces[1]
                self.piece_location['b'][rank][0], self.piece_location['g'][rank][0] = pieces[2], pieces[2]
                self.piece_location['c'][rank][0], self.piece_location['f'][rank][0] = pieces[3], pieces[3]
                self.piece_location['d'][rank][0], self.piece_location['e'][rank][0] = pieces[4], pieces[5]
            else:
                for col in "abcdefgh": self.piece_location[col][rank][0] = pieces[0]

    def get_capture_info(self, move_uci):
        """
        Détermine si un coup UCI est une capture.
        IMPORTANT: Appeler AVANT de push le move sur validation_board.

        Args:
            move_uci: Coup au format UCI (ex: 'e4d5')

        Returns:
            bool: True si c'est une capture, False sinon
        """
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.validation_board.legal_moves:
                # Vérifier si c'est une capture ou une prise en passant
                return self.validation_board.is_capture(move) or self.validation_board.is_en_passant(move)
            return False
        except:
            return False

    def log_move_to_file(self, move_uci, is_capture=False):
        """
        Logs the move to the communication file in the format 'W;e2e4;0' or 'B;e4d5;1'.

        Args:
            move_uci: Coup au format UCI
            is_capture: True si c'est une capture (défaut: False)
        """
        try:
            player_char = "B" if self.validation_board.turn == chess.WHITE else "W"
            capture_flag = "1" if is_capture else "0"
            with open(self.BESTMOVE_FILE, "w") as f:
                f.write(f"{player_char};{move_uci};{capture_flag}")
        except Exception as e:
            print(f"[ERROR] Could not write to {self.BESTMOVE_FILE}: {e}")

    # RENAMED: This is the turn logic specifically for Player vs AI mode.
    def play_turn_pve(self):
        """
        Handles a single turn for PVE mode.
        MODIFIED: Returns True if a move was made, False otherwise.
        """
        if self.winner: 
            return False

        human_color = self.player_color.lower()
        is_flipped = (human_color == 'black')
        board_turn_is_white = self.validation_board.turn == chess.WHITE

        # Si c'est le tour de l'humain
        if (board_turn_is_white and human_color == 'white') or \
        (not board_turn_is_white and human_color == 'black'):
            
            # handle_human_move retourne déjà True si un coup est joué, on propage juste la valeur
            return self.handle_human_move(human_color, is_flipped=is_flipped)
        
        # Si c'est le tour de l'IA
        else:
            if not self.stockfish_thinking:
                pygame.time.wait(200) # Petit délai avant que l'IA ne joue
                # run_stockfish_move retourne maintenant True si un coup est joué
                return self.run_stockfish_move()
                
        return False # Aucun coup n'a été joué dans cette frame

    # MODIFIED: This function now returns True if a move was successfully made.
    def handle_human_move(self, turn_color, is_flipped):
        """
        Manages mouse input for a human player.
        Returns True if a valid move was made, False otherwise.
        """
        square = self.get_selected_square(is_flipped)
        if not square:
            return False

        piece_name, columnChar, rowNo = square
        piece_color = piece_name[:5]

        # If a valid piece for the current turn is clicked
        if piece_name and piece_color == turn_color:
            for k in self.piece_location:
                for r in self.piece_location[k]:
                    self.piece_location[k][r][1] = False
            self.piece_location[columnChar][rowNo][1] = True
            
            # Highlight all legal moves for the selected piece
            legal_moves_uci = [move.uci() for move in self.validation_board.legal_moves]
            self.moves = []
            start_square = f"{columnChar}{rowNo}".lower()
            for move in legal_moves_uci:
                if move.startswith(start_square):
                    col_idx = ord(move[2]) - 97
                    row_idx = 8 - int(move[3])
                    self.moves.append([col_idx, row_idx])
            return False # Selecting a piece is not a move

        # If a move is being attempted (a piece is already selected)
        elif any(v[1] for val in self.piece_location.values() for v in val.values()):
            for k_from in self.piece_location:
                for r_from in self.piece_location[k_from]:
                    if self.piece_location[k_from][r_from][1]:
                        move_uci = f"{k_from}{r_from}{columnChar}{rowNo}".lower()
                        pawn_name = f"{turn_color}_pawn"
                        if self.piece_location[k_from][r_from][0] == pawn_name and (rowNo == 8 or rowNo == 1):
                            move_uci += 'q'

                        # Détecter si c'est une capture AVANT d'appliquer le coup
                        is_capture = self.get_capture_info(move_uci)

                        if self.validate_and_apply_move(move_uci):
                            # In PVP, log the move to the file for the other client
                            print(f"[{self.player_color}] Move made: {move_uci}. Logging to file.")
                            self.log_move_to_file(move_uci, is_capture)

                            # Attendre que le robot termine le coup (si activé)
                            if self.robot_wait_callback:
                                self.robot_wait_callback()

                            return True # A move was successfully made!
                        else:
                            # If move is illegal, just deselect the piece
                            self.piece_location[k_from][r_from][1] = False
                            self.moves = []
                        return False # An illegal move attempt is not a successful move
        return False

    def get_selected_square(self, is_flipped):
        """Gets board coordinates from a mouse click, accounting for board orientation."""
        if self.utils.left_click_event():
            mouse_pos = self.utils.get_mouse_event()
            for i in range(8):
                for j in range(8):
                    rect = pygame.Rect(self.board_locations[i][j][0], self.board_locations[i][j][1], self.square_length, self.square_length)
                    if rect.collidepoint(mouse_pos):
                        screen_col, screen_row = i, j
                        board_col = 7 - screen_col if is_flipped else screen_col
                        board_row = 7 - screen_row if is_flipped else screen_row
                        colChar = chr(97 + board_col)
                        rowNo = 8 - board_row
                        return [self.piece_location[colChar][rowNo][0], colChar, rowNo]
        return None

    def draw_pieces(self, is_flipped):
        """Draws all pieces and highlights, flipping the board view if required."""
        surface_blue = pygame.Surface((self.square_length, self.square_length), pygame.SRCALPHA)
        surface_blue.fill((28, 21, 212, 170)) # Highlight for White
        
        for screen_col in range(8):
            for screen_row in range(8):
                board_col_idx = 7 - screen_col if is_flipped else screen_col
                board_row_idx = 7 - screen_row if is_flipped else screen_row
                board_col_char = chr(97 + board_col_idx)
                board_row_num = 8 - board_row_idx
                
                value = self.piece_location[board_col_char][board_row_num]
                piece_name, is_selected, _ = value
                screen_pos = self.board_locations[screen_col][screen_row]

                if is_selected:
                    self.screen.blit(surface_blue, screen_pos)
                
                for move in self.moves:
                    if move[0] == board_col_idx and move[1] == board_row_idx:
                        self.screen.blit(surface_blue, screen_pos)
                        break

                if piece_name:
                    self.chess_pieces.draw(self.screen, piece_name, screen_pos)

    def validate_and_apply_move(self, move_uci):
        """Validates and applies any move using the python-chess board."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.validation_board.legal_moves:
                # CORRECTION: Vérifier le roque AVANT de push le move
                is_castling = self.validation_board.is_castling(move)
                is_en_passant = self.validation_board.is_en_passant(move)
                
                self.validation_board.push(move)
                self.apply_move_to_internal_board(move_uci, is_castling, is_en_passant)
                self.check_game_status()
                return True
            return False
        except Exception:
            return False

    def apply_move_to_internal_board(self, move_uci, is_castling, is_en_passant):
        """Applies a validated move to our internal board representation."""
        from_sq, to_sq = move_uci[:2], move_uci[2:4]
        from_file, from_rank = from_sq[0], int(from_sq[1])
        to_file, to_rank = to_sq[0], int(to_sq[1])
        piece_name = self.piece_location[from_file][from_rank][0]

        # Gérer la capture d'une pièce
        captured_piece = self.piece_location[to_file][to_rank][0]
        if captured_piece:  # S'il y a une pièce sur la case de destination
            if captured_piece.startswith('white'):
                self.black_captured.append(captured_piece)
            else:
                self.white_captured.append(captured_piece)

        self.piece_location[to_file][to_rank][0] = piece_name
        self.piece_location[from_file][from_rank][0] = ""
        
        move = chess.Move.from_uci(move_uci)
        
        # Gérer le roque
        if is_castling:
            if to_file == 'g':  # Petit roque (kingside)
                rook = self.piece_location['h'][to_rank][0]
                self.piece_location['f'][to_rank][0] = rook
                self.piece_location['h'][to_rank][0] = ""
                print(f"Petit roque effectué sur le rang {to_rank}")
            elif to_file == 'c':  # Grand roque (queenside)
                rook = self.piece_location['a'][to_rank][0]
                self.piece_location['d'][to_rank][0] = rook
                self.piece_location['a'][to_rank][0] = ""
                print(f"Grand roque effectué sur le rang {to_rank}")
        # Gérer la prise en passant
        elif is_en_passant:
            captured_pawn = self.piece_location[to_file][from_rank][0]
            if captured_pawn:
                if captured_pawn.startswith('white'):
                    self.black_captured.append(captured_pawn)
                else:
                    self.white_captured.append(captured_pawn)
            self.piece_location[to_file][from_rank][0] = ""
        # Gérer la promotion
        elif move.promotion:
            color = "white" if to_rank == 8 else "black"
            promoted_map = {chess.QUEEN: f"{color}_queen", chess.ROOK: f"{color}_rook", chess.BISHOP: f"{color}_bishop", chess.KNIGHT: f"{color}_knight"}
            self.piece_location[to_file][to_rank][0] = promoted_map[move.promotion]

        self.turn["white"], self.turn["black"] = self.turn["black"], self.turn["white"]
        self.moves = []
        for k in self.piece_location:
            for r in self.piece_location[k]:
                self.piece_location[k][r][1] = False
    
    def check_game_status(self):
        """Checks for game over conditions."""
        if self.validation_board.is_checkmate():
            self.winner = "Black" if self.validation_board.turn == chess.WHITE else "White"
        elif self.validation_board.is_game_over():
            self.winner = "Draw"

    def run_stockfish_move(self):
        """
        Gets and applies a move from the AI (PVE only).
        MODIFIED: Returns True if a move was successfully made, False otherwise.
        """
        if self.stockfish_thinking: 
            return False
            
        self.stockfish_thinking = True
        
        fen = self.validation_board.fen()
        bestmove_uci = self.engine_instance.get_best_move(fen)

        if not bestmove_uci:
            legal_moves = list(self.validation_board.legal_moves)
            if legal_moves:
                bestmove_uci = random.choice(legal_moves).uci()
            else:
                self.stockfish_thinking = False
                return False # Aucun coup possible

        is_capture = self.get_capture_info(bestmove_uci)
        
        # CORRECTION PRINCIPALE : On utilise une variable pour suivre si le coup a réussi
        move_was_successful = False
        if self.validate_and_apply_move(bestmove_uci):
            print(f"Stockfish plays: {bestmove_uci} (Capture: {is_capture})")
            self.log_move_to_file(bestmove_uci, is_capture)

            # Attendre que le robot termine le coup de Stockfish (si activé)
            if self.robot_wait_callback:
                self.robot_wait_callback()

            move_was_successful = True
        else:
            # Fallback si le coup de Stockfish est invalide (ne devrait pas arriver)
            print(f"[ERROR] Stockfish proposed an illegal move: {bestmove_uci}. Trying a random move.")
            legal_moves = list(self.validation_board.legal_moves)
            if legal_moves:
                random_move_uci = random.choice(legal_moves).uci()
                is_capture_fallback = self.get_capture_info(random_move_uci)
                if self.validate_and_apply_move(random_move_uci):
                    self.log_move_to_file(random_move_uci, is_capture_fallback)

                    # Attendre que le robot termine le coup (si activé)
                    if self.robot_wait_callback:
                        self.robot_wait_callback()

                    move_was_successful = True
        
        self.stockfish_thinking = False
        # On retourne la variable pour que le jeu sache s'il doit attendre le robot
        return move_was_successful