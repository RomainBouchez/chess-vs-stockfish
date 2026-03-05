import time
from typing import Dict, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from robot_chess_controller import ChessRobotController

class BoardResetter:
    """
    Service class responsible for resetting the chess board at the end of a game.
    It commands a ChessRobotController instance to physically move the pieces
    back to their initial positions, handling captured pieces and temporary parking.
    """

    INITIAL_BOARD = {
        "a1": {"color": "white", "type": "rook"},
        "b1": {"color": "white", "type": "knight"},
        "c1": {"color": "white", "type": "bishop"},
        "d1": {"color": "white", "type": "queen"},
        "e1": {"color": "white", "type": "king"},
        "f1": {"color": "white", "type": "bishop"},
        "g1": {"color": "white", "type": "knight"},
        "h1": {"color": "white", "type": "rook"},
        "a2": {"color": "white", "type": "pawn"},
        "b2": {"color": "white", "type": "pawn"},
        "c2": {"color": "white", "type": "pawn"},
        "d2": {"color": "white", "type": "pawn"},
        "e2": {"color": "white", "type": "pawn"},
        "f2": {"color": "white", "type": "pawn"},
        "g2": {"color": "white", "type": "pawn"},
        "h2": {"color": "white", "type": "pawn"},
        "a7": {"color": "black", "type": "pawn"},
        "b7": {"color": "black", "type": "pawn"},
        "c7": {"color": "black", "type": "pawn"},
        "d7": {"color": "black", "type": "pawn"},
        "e7": {"color": "black", "type": "pawn"},
        "f7": {"color": "black", "type": "pawn"},
        "g7": {"color": "black", "type": "pawn"},
        "h7": {"color": "black", "type": "pawn"},
        "a8": {"color": "black", "type": "rook"},
        "b8": {"color": "black", "type": "knight"},
        "c8": {"color": "black", "type": "bishop"},
        "d8": {"color": "black", "type": "queen"},
        "e8": {"color": "black", "type": "king"},
        "f8": {"color": "black", "type": "bishop"},
        "g8": {"color": "black", "type": "knight"},
        "h8": {"color": "black", "type": "rook"},
    }

    def __init__(self, robot: 'ChessRobotController'):
        self.robot = robot
        self.is_resetting = False

    def reset_board(self):
        """Remet physiquement toutes les pièces à leur position initiale."""
        if self.is_resetting:
            print("[RESET] Un reset est déjà en cours.")
            return

        print("\n" + "="*50)
        print("[RESET] DÉBUT DE LA PROCÉDURE DE RESET DU PLATEAU")
        print("="*50)
        self.is_resetting = True

        try:
            # --- Phase 1 : identifier les pièces à déplacer (Mal placées) ---
            pieces_to_park = []
            already_correct = set()

            # Parcourir le plateau actuel (la mémoire du robot)
            for square, piece in list(self.robot.board_state.items()):
                expected = self.INITIAL_BOARD.get(square)
                # La pièce est-elle exactement la bonne (Type + Couleur) sur la bonne case ?
                if expected and expected["type"] == piece["type"] and expected["color"] == piece["color"]:
                    already_correct.add(square)
                    print(f"[RESET] {piece['color']} {piece['type']} en {square} = Déjà à sa place.")
                else:
                    pieces_to_park.append({"square": square, **piece})

            print(f"\n[RESET] Phase 1 terminée : {len(already_correct)} pièces bien placées, {len(pieces_to_park)} à exfiltrer (Parking).")

            # --- Phase 2 : Parker les pièces mal placées (pour libérer le plateau) ---
            parked_pieces = []
            park_counter = 0

            for piece_info in pieces_to_park:
                source_pos = self.robot.uci_to_coordinates(piece_info["square"])
                park_coord = self.robot._get_temp_parking_position(park_counter)

                print(f"[RESET] Exfiltration: {piece_info['color']} {piece_info['type']} de {piece_info['square']} vers Parking #{park_counter}")
                self.robot._pick_and_place(source_pos, park_coord)

                parked_pieces.append({
                    "type": piece_info["type"],
                    "color": piece_info["color"],
                    "storage_pos": park_coord,
                })
                # Mise à jour de la mémoire du robot
                del self.robot.board_state[piece_info["square"]]
                park_counter += 1

            # --- Phase 3 : Rassembler TOUTES les pièces à replacer ---
            # Liste contenant pièces parquées + pièces capturées au cimetière
            all_pieces_to_place = parked_pieces + self.robot.captured_pieces
            print(f"\n[RESET] Phase 2/3 terminées : {len(all_pieces_to_place)} pièces attendent d'être repositionnées.")

            # --- Phase 4 : Parcourir le plateau idéal et le remplir physiquement ---
            placed_squares = set(already_correct)

            for target_square, expected_piece in self.INITIAL_BOARD.items():
                if target_square in placed_squares:
                    continue

                # Chercher une pièce correspondante (Couleur + Type) dans la liste d'attente
                match_idx = None
                match_piece = None

                for i, p in enumerate(all_pieces_to_place):
                    if p["type"] == expected_piece["type"] and p["color"] == expected_piece["color"]:
                        match_idx = i
                        match_piece = p
                        break

                if match_piece:
                    source_pos = match_piece["storage_pos"]
                    dest_pos = self.robot.uci_to_coordinates(target_square)

                    print(f"[RESET] Repositionnement: {expected_piece['color']} {expected_piece['type']} vers sa case origine {target_square}")
                    self.robot._pick_and_place(source_pos, dest_pos)

                    # Retirer la pièce du groupe d'attente (elle est désormais placée)
                    all_pieces_to_place.pop(match_idx)
                    placed_squares.add(target_square)
                else:
                    print(f"[RESET][ERREUR] Pièce manquante ({expected_piece['color']} {expected_piece['type']}) introuvable dans le cimetière ou le parking pour la case {target_square} !")

            # --- Phase 5 : Finalisation de la mémoire et Repos ---
            print("\n[RESET] Tous les repositionnements sont terminés. Finalisation...")
            # Effacer les compteurs de captures et sauvegarder l'etat à zero
            self.robot.captured_pieces.clear()
            self.robot.white_capture_count = 0
            self.robot.black_capture_count = 0
            self.robot.save_state()

            # Remettre le plateau logiciel du robot à l'état initial
            self.robot.init_board_state()

            # Retour à la base (coin A1 avec Z levé)
            self.robot.home_robot()

            print("[RESET] PROCÉDURE DE RESET TERMINÉE AVEC SUCCÈS.")
        
        except Exception as e:
            print(f"[RESET][ERREUR CRITIQUE] La procédure de reset a échoué: {e}")
        finally:
            self.is_resetting = False
