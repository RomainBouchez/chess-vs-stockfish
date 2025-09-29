from game_with_stockfish import Game

if __name__=="__main__":
    print("Lancement de Chess vs Stockfish...")
    print("Vous jouez les pièces blanches.")
    print("Assurez-vous que les fichiers suivants sont présents :")
    print("- uci_stockfish.py (votre script Stockfish)")
    print("- piece.py, utils.py")
    print("- Dossier 'res/' avec board.png et pieces.png (optionnel)")
    print()
    
    game = Game()
    game.start_game()