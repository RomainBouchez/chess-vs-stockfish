#!/usr/bin/env python3
"""
Debug pour voir pourquoi les coups de Stockfish ne sont pas appliqués
"""

import os

def debug_bestmove():
    """Debug le contenu du fichier bestmove.txt"""

    print("DEBUG: Analyse du fichier bestmove.txt")
    print("=" * 40)

    bestmove_file = "bestmove.txt"

    if os.path.exists(bestmove_file):
        with open(bestmove_file, "r") as f:
            content = f.read()

        print(f"Contenu brut: '{content}'")
        print(f"Contenu après strip(): '{content.strip()}'")
        print(f"Longueur: {len(content.strip())}")

        bestmove = content.strip()

        if len(bestmove) >= 4:
            print(f"✓ Format valide: {bestmove}")

            # Analyser le coup UCI
            from_square = bestmove[:2]
            to_square = bestmove[2:4]
            promotion = bestmove[4:] if len(bestmove) > 4 else ""

            print(f"  De: {from_square}")
            print(f"  Vers: {to_square}")
            if promotion:
                print(f"  Promotion: {promotion}")

            # Tester la validation chess
            try:
                import chess
                move = chess.Move.from_uci(bestmove)
                print(f"✓ Coup UCI valide: {move}")
            except Exception as e:
                print(f"✗ Coup UCI invalide: {e}")

        else:
            print(f"✗ Format invalide (longueur: {len(bestmove)})")

    else:
        print("✗ Fichier bestmove.txt n'existe pas")

    print("\n" + "=" * 40)
    print("Pour tester:")
    print("1. Lancez le jeu")
    print("2. Faites un coup")
    print("3. Exécutez ce script pendant que Stockfish réfléchit")

def test_move_validation():
    """Teste la validation d'un coup spécifique"""

    print("\nTEST: Validation de coup")
    print("=" * 30)

    # Position de test (après d2-d4)
    test_fen = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"
    test_move = "e7e6"  # Coup typique de Stockfish

    try:
        import chess

        board = chess.Board(test_fen)
        print(f"Position de test: {test_fen}")
        print(f"Coup de test: {test_move}")

        move = chess.Move.from_uci(test_move)

        if move in board.legal_moves:
            print("✓ Coup légal")

            # Appliquer le coup
            board.push(move)
            print(f"Nouvelle position: {board.fen()}")

        else:
            print("✗ Coup illégal")
            legal_moves = [m.uci() for m in board.legal_moves]
            print(f"Coups légaux: {legal_moves[:10]}...")

    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_bestmove()
    test_move_validation()