
# Données des bots pour le nouveau menu de sélection
# Structure: Liste de catégories, chaque catégorie a un nom et une liste de bots.
# Chaque bot a un nom, un Elo, et une description.

BOT_CATEGORIES = [
    {
        "name": "Beginner (250-800)",
        "color": (100, 200, 100), # Vert
        "bots": [
            {"name": "Martin", "elo": 250, "description": "Playing chess for the first time. Go easy!"},
            {"name": "Elani", "elo": 400, "description": "Learning the moves but still drops pieces."},
            {"name": "Aron", "elo": 700, "description": "Knows some basic tactics but makes mistakes."},
            {"name": "Emir", "elo": 1000, "description": "Getting better! Watch out for forks."}
        ]
    },
    {
        "name": "Intermediate (1200-1600)",
        "color": (255, 200, 0), # Jaune/Orange
        "bots": [
            {"name": "Sven", "elo": 1100, "description": "Solid player, doesn't give pieces away for free."},
            {"name": "Nelson", "elo": 1300, "description": "Aggressive with the Queen. Don't panic!"},
            {"name": "Antonio", "elo": 1500, "description": "Positional player. Hard to break down."},
            {"name": "Isabel", "elo": 1600, "description": "Tactically sharp. Calculates deeper."}
        ]
    },
    {
        "name": "Advanced (1800-2200)",
        "color": (255, 100, 0), # Orange foncé
        "bots": [
            {"name": "Wally", "elo": 1800, "description": "Very strong club player. Few mistakes."},
            {"name": "Li", "elo": 2000, "description": "Expert level. Knows theory well."},
            {"name": "Noam", "elo": 2200, "description": "Candidate Master strength. Very tricky."}
        ]
    },
    {
        "name": "Master (2300+)",
        "color": (200, 50, 50), # Rouge
        "bots": [
            {"name": "Francis", "elo": 2300, "description": "FIDE Master. Ruthless in endgames."},
            {"name": "Hikaru", "elo": 2700, "description": "Grandmaster speed demon."},
            {"name": "Magnus", "elo": 2850, "description": "The GOAT. Good luck."},
            {"name": "Stockfish 16", "elo": 3200, "description": "Maximum strength. The machine itself."}
        ]
    }
]
