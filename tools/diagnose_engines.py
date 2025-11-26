#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état des moteurs installés
"""

import os
import subprocess
from pathlib import Path
from engine_manager import EngineManager

def diagnose_engines():
    """Diagnostique tous les moteurs installés"""

    print("🔍 Diagnostic des moteurs d'échecs")
    print("=" * 50)

    engine_manager = EngineManager()

    # Vérifier le dossier engines
    engines_dir = engine_manager.engines_dir
    print(f"📁 Dossier moteurs: {engines_dir}")

    if not engines_dir.exists():
        print("❌ Le dossier engines n'existe pas")
        return

    print("✅ Dossier engines trouvé")
    print()

    # Lister tous les moteurs installés
    installed = engine_manager.get_installed_engines()
    print(f"📋 Moteurs installés: {len(installed)}")

    if not installed:
        print("❌ Aucun moteur installé")
        return

    # Diagnostiquer chaque moteur
    for engine_id, engine_info in installed.items():
        print(f"\n🔧 Diagnostic de {engine_id}")
        print("-" * 30)

        # Vérifier le chemin
        engine_path = engine_info.get("path")
        print(f"📍 Chemin configuré: {engine_path}")

        if not engine_path:
            print("❌ Aucun chemin configuré")
            continue

        # Vérifier l'existence du fichier
        if os.path.exists(engine_path):
            print("✅ Fichier existe")

            # Vérifier les permissions
            if os.access(engine_path, os.X_OK):
                print("✅ Fichier exécutable")
            else:
                print("⚠️  Fichier non exécutable")

            # Taille du fichier
            size_mb = os.path.getsize(engine_path) / (1024 * 1024)
            print(f"📊 Taille: {size_mb:.1f} MB")

            # Test de communication UCI
            print("🧪 Test UCI...")
            if test_uci_communication(engine_path):
                print("✅ Communication UCI OK")
            else:
                print("❌ Échec communication UCI")

        else:
            print("❌ Fichier n'existe pas")

            # Chercher dans le dossier
            engine_dir = engines_dir / engine_id
            if engine_dir.exists():
                print(f"📁 Contenu du dossier {engine_dir}:")
                find_executables_in_dir(engine_dir)
            else:
                print(f"❌ Dossier {engine_dir} n'existe pas")

def find_executables_in_dir(directory):
    """Trouve tous les exécutables dans un dossier"""
    executables = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, directory)

            # Sur Windows, chercher les .exe
            if os.name == 'nt' and file.endswith('.exe'):
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                print(f"   🎯 {relative_path} ({size_mb:.1f} MB)")
                executables.append(full_path)
            # Sur Unix, chercher les fichiers exécutables
            elif os.name != 'nt' and os.access(full_path, os.X_OK):
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                print(f"   🎯 {relative_path} ({size_mb:.1f} MB)")
                executables.append(full_path)

    if not executables:
        print("   ❌ Aucun exécutable trouvé")

    return executables

def test_uci_communication(engine_path):
    """Test simple de communication UCI"""
    try:
        # Lancer le moteur
        process = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

        # Envoyer "uci" et attendre "uciok"
        stdout, stderr = process.communicate(input="uci\nquit\n", timeout=5)

        if "uciok" in stdout.lower():
            return True
        else:
            print(f"   ⚠️  Réponse inattendue: {stdout[:100]}...")
            return False

    except subprocess.TimeoutExpired:
        print("   ⚠️  Timeout lors du test UCI")
        try:
            process.kill()
        except:
            pass
        return False
    except Exception as e:
        print(f"   ⚠️  Erreur UCI: {e}")
        return False

def suggest_fixes():
    """Suggère des corrections"""
    print("\n" + "=" * 50)
    print("💡 Suggestions de correction")
    print("=" * 50)

    engine_manager = EngineManager()
    installed = engine_manager.get_installed_engines()

    for engine_id, engine_info in installed.items():
        engine_path = engine_info.get("path")

        if not engine_path or not os.path.exists(engine_path):
            print(f"\n🔧 Pour {engine_id}:")

            # Chercher des exécutables alternatifs
            engine_dir = engine_manager.engines_dir / engine_id
            if engine_dir.exists():
                executables = find_executables_in_dir(engine_dir)

                if executables:
                    print("   Exécutables trouvés:")
                    for exe in executables[:3]:  # Montrer max 3
                        print(f"   • {exe}")

                    print("   💡 Vous pouvez:")
                    print("   1. Désinstaller et réinstaller ce moteur")
                    print("   2. Ou modifier manuellement engines_config.json")
                else:
                    print("   💡 Réinstallation recommandée")
            else:
                print("   💡 Réinstallation nécessaire")

if __name__ == "__main__":
    diagnose_engines()
    suggest_fixes()

    print("\n" + "=" * 50)
    print("✅ Diagnostic terminé")