    
# ♟️ Chess vs Stockfish

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-green?style=for-the-badge&logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.6-orange?style=for-the-badge&logo=pygame)
![Stockfish](https://img.shields.io/badge/Engine-Stockfish-red?style=for-the-badge)

**Jeu d'échecs en Python avec une interface Pygame, un moteur Stockfish configurable, et un mode 1v1 innovant sur deux écrans.**

</div>

## À Propos du Projet

**Chess vs Stockfish** est une implémentation complète du jeu d'échecs, développée en Python et destinée aux amateurs d'échecs et aux développeurs. Il se distingue par son interface soignée construite avec Pygame, son intégration robuste du moteur d'échecs de renommée mondiale **Stockfish**, et surtout, son mode multijoueur local unique.

Ce mode 1v1 lance deux instances distinctes du jeu, synchronisées par un système de communication simple, permettant une expérience de jeu sur deux écrans. Cette fonctionnalité a été initialement conçue pour des installations physiques, comme un robot échiquier contrôlé par deux tablettes.

## Images
### Main menu
![alt text](img/main_menu.png)

### Play against Stockfish 
![alt text](img/play_vs_stockfish.png)

### 1 vs 1
![alt text](img/1v1.png)
## ✨ Fonctionnalités Principales

### Modes de Jeu
*   **Solo contre l'IA** : Affrontez une version configurable de Stockfish. Idéal pour s'entraîner et analyser ses parties.
*   **1v1 Local (Deux Écrans)** : Lancez deux fenêtres de jeu indépendantes. Le plateau du joueur Noir est automatiquement retourné pour une perspective optimale.

### Moteur d'Échecs et Règles
*   ✅ **Validation Complète** : Utilise `python-chess` pour une validation rigoureuse de chaque coup, incluant les mouvements spéciaux (roque, prise en passant, promotion).
*   🏆 **Détection de Fin de Partie** : Gestion automatique de l'échec et mat, du pat, de la règle des 50 coups, de la triple répétition et du matériel insuffisant.
*   ⚙️ **Moteur Configurable** : Ajustez facilement le niveau de l'IA via une interface dédiée (niveau ELO, temps de réflexion, etc.).

### Technique et Robustesse
*   🎨 **Interface Moderne** : Une interface utilisateur sombre, propre et intuitive pour tous les menus et écrans de jeu.
*   🔄 **Gestion d'Erreurs** : Le système est conçu pour être résilient, avec un mode de secours qui active une IA aléatoire si le moteur Stockfish rencontre des erreurs répétées.
*   📁 **Communication Inter-Processus** : Le mode 1v1 utilise un système de communication basé sur un fichier (`next_move.txt`) pour synchroniser l'état de la partie entre les deux instances de jeu.

---

## 🛠️ Stack Technique

*   **Langage** : Python 3.12+
*   **Interface Graphique** : Pygame
*   **Logique d'Échecs** : `python-chess`
*   **Moteur d'IA** : Stockfish (géré via un gestionnaire de moteurs intégré)

---

## 🏗️ Architecture

Le projet est structuré autour d'un lanceur central qui dirige vers les différents modes de jeu.

```
                      +-----------------------+
                      |   main_stockfish.py   |
                      | (Point d'entrée)      |
                      +-----------+-----------+
                                  |
                   +--------------+--------------+
                   |                             |
         CHOIX DE MODE: PVE             CHOIX DE MODE: PVP
                   |                             |
                   |                +----------------------------+
                   |                | Lance 2 processus de       |
                   |                | game_with_stockfish.py     |
                   |                +-------------+--------------+
                   |                              |
                   | (Instance unique)            | (Client Blanc & Client Noir)
                   |                              |
                   +--------------+---------------+
                                  |
                      +-----------v-----------+
                      | game_with_stockfish.py|
                      | (Boucle de jeu, UI)   |
                      +-----------+-----------+
                                  |
                      +-----------v-----------+
                      | chess_with_validation.py|
                      | (Logique, validation) |
                      +-----------+-----------+
                                  |
           +----------------------+----------------------+
           |                      |                      |
+----------v---------+ +----------v----------+ +---------v----------+
|   python-chess     | |    next_move.txt    | |   uci_stockfish.py |
|    (Validation)    | |    (Synchro 1v1)    | | (Communication IA) |
+--------------------+ +---------------------+ +----------+---------+
                                                         |
                                             +-----------v----------+
                                             |   Stockfish Engine   |
                                             |     (exécutable)     |
                                             +----------------------+
```

    
#### Communication
*   **Mode IA (PVE)** : La communication avec le moteur Stockfish se fait via des `subprocess` qui exécutent le moteur en arrière-plan.
*   **Mode 1v1 (PVP)** : La synchronisation entre les deux fenêtres de jeu est assurée par un fichier (`next_move.txt`) agissant comme un canal de communication inter-processus (IPC) simple mais efficace.

---

## 🚀 Démarrage Rapide

### Prérequis
Assurez-vous d'avoir Python 3.12 ou une version plus récente installée.

### Installation
1.  **Clonez le dépôt :**
    ```sh
    git clone https://github.com/romainbouchez/chess-vs-stockfish.git
    cd chess-vs-stockfish
    ```
2.  **Installez les dépendances :**
    ```sh
    pip install -r requirements.txt
    ```

---

## 🎮 Utilisation

1.  **Lancez l'application :**
    ```sh
    python main_stockfish.py
    ```
2.  **Choisissez un mode de jeu :**
    *   **Play vs Stockfish** : Ouvre le menu des paramètres de l'IA. Cliquez sur "Play" pour commencer votre partie contre l'ordinateur.
    *   **Play 1v1 (2 Screens)** : Ferme le menu principal et lance immédiatement deux nouvelles fenêtres, une pour chaque joueur.

---

## ⚙️ Configuration de l'IA

La difficulté et le comportement du moteur Stockfish peuvent être ajustés directement depuis l'interface :
1.  Lancez le jeu et choisissez `Play vs Stockfish`.
2.  Cliquez sur le bouton **Settings**.
3.  Utilisez les sliders pour configurer le **niveau ELO** ou accédez aux paramètres avancés pour plus de contrôle (threads, mémoire, etc.).
4.  Le menu **Engines** vous permet de télécharger et de gérer différentes versions de Stockfish.

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! Si vous souhaitez améliorer ce projet, veuillez suivre les étapes suivantes :

1.  **Forkez le projet** sur GitHub.
2.  **Créez une nouvelle branche** pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`).
3.  **Commitez vos changements** (`git commit -m 'Add some AmazingFeature'`).
4.  **Pushez vers la branche** (`git push origin feature/AmazingFeature`).
5.  **Ouvrez une Pull Request**.

---

## 📞 Contact

**Romain BOUCHEZ** - bouchez@et.esiea.fr

Lien du projet : [https://github.com/romainbouchez/chess-vs-stockfish](https://github.com/romainbouchez/chess-vs-stockfish)