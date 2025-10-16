import sys
import os
from universal_engine import get_universal_engine

# === CONFIGURATION ===
OUTPUT_FILE = "next_move.txt"

def main():
    # Obtenir l'instance du moteur universel
    engine = get_universal_engine()
    
    # Initialiser le moteur
    if not engine.initialize():
        sys.exit(1)

    # Lire FEN passée en argument
    if len(sys.argv) > 1:
        fen = sys.argv[1]
    else:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # Position de départ

    # Obtenir le meilleur coup
    bestmove = engine.get_best_move(fen)
    
    if bestmove is None:
        print("[ERREUR] Le moteur n'a pas trouvé de coup")
        sys.exit(1)

    # Écrire dans next_move.txt
    with open(OUTPUT_FILE, "w") as f:
        f.write(f"B;{bestmove}")

    print(f"Meilleur coup : {bestmove} (écrit dans {OUTPUT_FILE})")


if __name__ == "__main__":
    main()