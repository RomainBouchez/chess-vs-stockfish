#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification de toutes les dépendances du projet
Lance ce script pour identifier les modules manquants
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Liste de TOUS les modules externes utilisés dans le projet
REQUIRED_MODULES = {
    'pygame': 'Interface graphique (OBLIGATOIRE)',
    'chess': 'Logique d\'échecs via python-chess (OBLIGATOIRE)',
    'requests': 'Téléchargement de Stockfish (OBLIGATOIRE)',
}

OPTIONAL_MODULES = {
    'serial': 'Communication série pour robot (OPTIONNEL)',
}

def check_module(module_name, description):
    """Vérifie si un module peut être importé"""
    try:
        __import__(module_name)
        return True, f"[OK] {module_name}: {description}"
    except ImportError:
        return False, f"[MANQUANT] {module_name}: {description}"

def main():
    print("=" * 70)
    print("VÉRIFICATION DES DÉPENDANCES - Chess vs Stockfish")
    print("=" * 70)
    print()

    # Vérifier Python version
    print(f"Version Python: {sys.version}")
    if sys.version_info < (3, 12):
        print("[ATTENTION] Python 3.12+ recommande (vous avez {}.{})".format(
            sys.version_info.major, sys.version_info.minor))
    else:
        print("[OK] Version Python correcte")
    print()

    # Vérifier les modules obligatoires
    print("MODULES OBLIGATOIRES:")
    print("-" * 70)

    all_required_ok = True
    missing_required = []

    for module, desc in REQUIRED_MODULES.items():
        ok, msg = check_module(module, desc)
        print(msg)
        if not ok:
            all_required_ok = False
            missing_required.append(module)

    print()

    # Vérifier les modules optionnels
    print("MODULES OPTIONNELS:")
    print("-" * 70)

    for module, desc in OPTIONAL_MODULES.items():
        ok, msg = check_module(module, desc)
        print(msg)

    print()
    print("=" * 70)

    # Résultat final
    if all_required_ok:
        print("SUCCES: Toutes les dependances obligatoires sont installees!")
        print()
        print("Vous pouvez maintenant lancer:")
        print("  python main_stockfish.py")
        return 0
    else:
        print("ECHEC: Des dependances obligatoires sont manquantes!")
        print()
        print("Installez-les avec:")
        print("  pip install -r requirements.txt")
        print()
        print(f"Modules manquants: {', '.join(missing_required)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
