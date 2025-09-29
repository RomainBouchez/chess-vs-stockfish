import sys
import os
import chess
import chess.engine

# === CONFIGURATION ===
ENGINE_PATH = r"C:\Users\romai\Documents\1._Romain\2_Esiea\4A\PST\dist\stockfish.exe"
SEARCH_TIME = 0.5  # Réduit à 0.5s pour éviter les timeouts
OUTPUT_FILE = "bestmove.txt"


def main():
    # Vérif du binaire
    if not os.path.isfile(ENGINE_PATH):
        print(f"[ERREUR] Stockfish introuvable à : {ENGINE_PATH}")
        sys.exit(1)

    engine = None
    try:
        # Configuration plus conservatrice pour éviter les crashes
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
        engine.configure({
            "Threads": 1,        # Réduit de 4 à 1 thread
            "Hash": 64,          # Réduit de 512 à 64 MB
            "Skill Level": 15    # Niveau de jeu (1-20, 20 = maximum)
        })
    except Exception as e:
        print(f"[ERREUR] Impossible de lancer Stockfish : {e}")
        if engine:
            try:
                engine.quit()
            except:
                pass
        sys.exit(1)

    # Lire FEN passée en argument
    if len(sys.argv) > 1:
        fen = sys.argv[1]
        try:
            board = chess.Board(fen)
            
            # Vérifier que la position est valide
            if not board.is_valid():
                print(f"[ERREUR] Position FEN invalide : {fen}")
                engine.quit()
                sys.exit(1)
                
        except Exception as e:
            print(f"[ERREUR] FEN invalide : {fen} - {e}")
            engine.quit()
            sys.exit(1)
    else:
        board = chess.Board()

    try:
        # Demande à Stockfish le meilleur coup avec timeout plus court
        result = engine.play(board, chess.engine.Limit(time=SEARCH_TIME))
        
        if result.move is None:
            print("[ERREUR] Stockfish n'a pas trouvé de coup")
            engine.quit()
            sys.exit(1)
            
        bestmove = result.move.uci()

        # Écrire dans bestmove.txt
        with open(OUTPUT_FILE, "w") as f:
            f.write(bestmove)

        print(f"Meilleur coup : {bestmove} (écrit dans {OUTPUT_FILE})")

    except chess.engine.EngineTerminatedError:
        print("[ERREUR] Stockfish s'est arrêté de manière inattendue")
        sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'analyse : {e}")
        sys.exit(1)
    finally:
        # S'assurer que le moteur se ferme proprement
        if engine:
            try:
                engine.quit()
            except:
                pass


if __name__ == "__main__":
    main()