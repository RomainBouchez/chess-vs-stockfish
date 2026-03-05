import os
import sys

# Ajouter le répertoire courant au PYTHONPATH pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_manager import EngineManager

def check_and_install():
    print("Vérification de l'installation de Stockfish...")
    try:
        em = EngineManager()
        
        # Le moteur par défaut est stockfish_latest
        engine_id = "stockfish_latest"
        
        # Vérifier si l'exécutable fonctionne
        is_working = em.verify_engine(engine_id)
        
        if is_working:
            print("Stockfish est déjà installé et fonctionnel !")
            return

        print("Stockfish n'est pas installé ou ne fonctionne pas. Installation en cours...")
        
        # Désinstaller s'il était listé mais défectueux
        if em.is_engine_installed(engine_id):
            print("Nettoyage de l'ancienne installation...")
            em.uninstall_engine(engine_id)
            
        # Télécharger et installer
        em.download_engine(engine_id)
        
        if not em.verify_engine(engine_id):
            print("\n[ATTENTION] Stockfish a été téléchargé mais ne fonctionne toujours pas.")
            print("Il est possible que votre processeur soit ancien et ne supporte pas l'architecture AVX2.")
            print("Dans ce cas, vous devrez télécharger manuellement une version 'popcnt' ou 'x64-old' depuis le site officiel de Stockfish et écraser le fichier .exe dans 'engines/stockfish_latest/stockfish/'.\n")
        else:
            print("Installation de Stockfish terminée avec succès !")
        
        # Mettre à jour selected_engine.txt
        with open("selected_engine.txt", "w") as f:
            f.write(engine_id)

        
    except Exception as e:
        print(f"Erreur lors de la vérification/installation de Stockfish: {e}")

if __name__ == "__main__":
    check_and_install()
