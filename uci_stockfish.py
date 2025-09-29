import sys
import os
import chess
import chess.engine
from settings import StockfishSettings

# === CONFIGURATION ===
ENGINE_PATH = r"C:\Users\romai\Documents\1._Romain\2_Esiea\4A\PST\dist\stockfish.exe"
OUTPUT_FILE = "bestmove.txt"


def main():
    # Charger les paramètres depuis le fichier de configuration
    settings = StockfishSettings()
    
    # Vérif du binaire
    if not os.path.isfile(ENGINE_PATH):
        print(f"[ERREUR] Stockfish introuvable à : {ENGINE_PATH}")
        sys.exit(1)

    engine = None
    try:
        # Lancer Stockfish
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
        
        # Appliquer la configuration depuis les paramètres
        engine_config = settings.get_engine_config()
        print(f"Configuration Stockfish : {engine_config}")
        print(f"ELO approximatif : {settings.get_elo()}")
        
        engine.configure(engine_config)
        
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
        # Obtenir les limites de recherche depuis les paramètres
        search_limits = settings.get_search_limit()
        print(f"Limites de recherche : {search_limits}")
        
        # Créer l'objet Limit
        limit_kwargs = {}
        if "time" in search_limits:
            limit_kwargs["time"] = search_limits["time"]
        if "depth" in search_limits:
            limit_kwargs["depth"] = search_limits["depth"]
        
        limit = chess.engine.Limit(**limit_kwargs)
        
        # Demander le meilleur coup
        result = engine.play(board, limit)
        
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