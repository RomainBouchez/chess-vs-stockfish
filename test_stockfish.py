#!/usr/bin/env python3
"""
Test simple pour vérifier que Stockfish fonctionne
"""

import os
import subprocess
from engine_manager import EngineManager

def test_stockfish_simple():
    """Test simple de Stockfish"""

    print("Test de Stockfish")
    print("=" * 30)

    engine_manager = EngineManager()

    # Vérifier l'installation
    if not engine_manager.is_engine_installed("stockfish_latest"):
        print("ERREUR: Stockfish latest non installé")
        return False

    # Obtenir le chemin
    stockfish_path = engine_manager.get_engine_path("stockfish_latest")
    print(f"Chemin: {stockfish_path}")

    # Vérifier l'existence
    if not os.path.exists(stockfish_path):
        print("ERREUR: Fichier n'existe pas")
        return False

    print("OK: Fichier existe")

    # Test UCI
    print("Test communication UCI...")
    try:
        process = subprocess.Popen(
            [stockfish_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input="uci\nquit\n", timeout=10)

        if "uciok" in stdout:
            print("OK: Communication UCI reussie")
            return True
        else:
            print("ERREUR: Pas de reponse UCI")
            print(f"Sortie: {stdout[:200]}")
            return False

    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    if test_stockfish_simple():
        print("\nSUCCES: Stockfish fonctionne!")
    else:
        print("\nECHEC: Stockfish ne fonctionne pas")