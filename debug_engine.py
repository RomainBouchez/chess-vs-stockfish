#!/usr/bin/env python3
"""
Debug des paramètres moteur
"""

from universal_settings import UniversalEngineSettings
from universal_engine import get_universal_engine

def debug_engine_settings():
    """Debug complet des paramètres du moteur"""

    print("DEBUG: Paramètres du moteur")
    print("=" * 40)

    # Universal settings
    universal_settings = UniversalEngineSettings()

    current_engine = universal_settings.get_selected_engine()
    print(f"Moteur sélectionné: {current_engine}")

    # Paramètres bruts
    engine_settings = universal_settings.get_engine_settings()
    print(f"Paramètres bruts: {engine_settings}")

    # Configuration UCI
    uci_config = universal_settings.get_uci_config()
    print(f"Configuration UCI: {uci_config}")

    # Limites de recherche
    search_limits = universal_settings.get_search_limits()
    print(f"Limites de recherche: {search_limits}")

    print("\n" + "=" * 40)
    print("TEST: Moteur universel")
    print("=" * 40)

    # Test avec le moteur universel
    engine = get_universal_engine()

    if engine.initialize():
        print("✓ Moteur initialisé")

        # Test avec une position simple
        fen = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"
        print(f"Position de test: {fen}")

        import time
        start_time = time.time()

        bestmove = engine.get_best_move(fen)

        end_time = time.time()
        elapsed = end_time - start_time

        print(f"Temps écoulé: {elapsed:.2f}s")
        print(f"Meilleur coup: {bestmove}")

        if elapsed > 5.0:
            print("PROBLÈME: Le moteur prend trop de temps!")
        else:
            print("OK: Temps de réponse acceptable")
    else:
        print("✗ Échec initialisation moteur")

if __name__ == "__main__":
    debug_engine_settings()