# Documentation de Passation - Robot Joueur d'Échecs

> **Document destiné aux futurs étudiants** qui reprendront ce projet.
> Dernière mise à jour : Janvier 2026

---

## Table des matières

1. [Présentation du projet](#1-présentation-du-projet)
2. [Architecture matérielle](#2-architecture-matérielle)
3. [Architecture logicielle](#3-architecture-logicielle)
4. [Configuration Marlin (Firmware)](#4-configuration-marlin-firmware)
5. [Calibration de la machine](#5-calibration-de-la-machine)
6. [Utilisation du robot avec le jeu](#6-utilisation-du-robot-avec-le-jeu)
7. [État actuel du projet](#7-état-actuel-du-projet)
8. [Améliorations futures](#8-améliorations-futures)
9. [Problèmes connus et solutions](#9-problèmes-connus-et-solutions)
10. [Ressources et liens utiles](#10-ressources-et-liens-utiles)

---

## 1. Présentation du projet

### Objectif

Ce projet consiste à créer un **robot joueur d'échecs** capable de :
- Jouer physiquement des parties d'échecs contre un humain
- Utiliser le moteur Stockfish pour calculer les meilleurs coups
- Déplacer les pièces sur un échiquier réel via une machine à commande numérique

### Contexte

- **Type de projet** : PST (Projet Scientifique et Technique) - ESIEA
- **Base matérielle** : Structure d'imprimante 3D
- **Contrôleur** : Carte MKS Gen V1.4 avec firmware Marlin

### Principe de fonctionnement

```
┌─────────────────┐      ┌─────────────────┐       ┌─────────────────┐
│   Interface     │      │    Scripts      │       │     Robot       │
│   Graphique     │────▶│    Python       │ ────▶ │   (G-code)      │
│   (Pygame)      │      │                 │       │                 │
└─────────────────┘      └─────────────────┘       └─────────────────┘
        │                        │                         │
        │                        │                         │
        ▼                        ▼                         ▼
   Joueur humain          Stockfish              Échiquier physique
   fait son coup          calcule le            Le robot déplace
                          meilleur coup         les pièces
```

---

## 2. Architecture matérielle

### 2.1 Composants principaux

| Composant | Modèle/Type | Rôle |
|-----------|-------------|------|
| Carte contrôleur | **MKS Gen V1.4** | Pilote les moteurs et reçoit les commandes G-code |
| Moteurs pas-à-pas | NEMA 17 (x3) | Axes X, Y et Z |
| Fins de course | Endstops (x2 actuellement) | Homing des axes X et Y |
| Système de préhension | Servo + Pince | Attraper et relâcher les pièces |
| Alimentation | 20V | Alimentation des moteurs stepper |
| Écran LCD | 128x64 (optionnel) | Affichage de debug |

### 2.2 Schéma de câblage

Voici la description du câblage sur la carte MKS Gen V1.4 :

```
┌────────────────────────────────────────────────────────────────┐
│                      MKS Gen V1.4                              │
│                                                                │
│  [ROSE] ──────────▶ Alimentation 20V (moteurs stepper)        │
│                                                                │
│  [VIOLET] ────────▶ USB vers PC (G-code + upload firmware)    │
│                                                                │
│  [BLEU] ──────────▶ Connecteur moteur Axe X                   │
│                                                                │
│  [VERT] ──────────▶ Connecteur moteur Axe Y                   │
│                                                                │
│  [JAUNE] ─────────▶ Connecteur moteur Axe Z                   │
│                                                                │
│  [ROUGE] ─────────▶ Connecteurs fins de course (endstops)     │
│                                                                │
│  [ORANGE] ────────▶ Emplacement servo pince (à connecter)     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 Zones de capture des pièces

Les pièces capturées sont placées sur les côtés de l'échiquier dans des grilles 2x4 :

```

 

┌─────────────────────────┐
│Zone N │         │Zone N │  ← Pièces NOIRES capturées (côté noir)
│ 2x4   │ PLATEAU │ 2x4   │
│gauche │ 8x8     │droite │
├───────┼─────────┼───────┤
│Zone B │         │Zone B │
│ 2x4   │         │ 2x4   │
│gauche │         │droite │  ← Pièces BLANCHES capturées (côté blanc)
└─────────────────────────┘
          

```

---

## 3. Architecture logicielle

### 3.1 Structure du projet

```
chess-vs-stockfish/
│
├── main_stockfish.py           # Point d'entrée principal
├── game_with_stockfish.py      # Boucle de jeu et interface Pygame
├── chess_with_validation.py    # Logique d'échecs et validation
│
├── G-Code_Controller/          # ⭐ CONTRÔLE DU ROBOT
│   ├── robot_chess_controller.py   # Contrôleur principal du robot
│   ├── robot_calibration.py        # Script de calibration
│   ├── robot_config.ini            # Configuration du robot
│   ├── calibration_ramps.py        # Tests de rampes
│   ├── calibrate_servo_values.py   # Calibration servo
│   └── test_servo_z.py             # Test axe Z
│
├── tools/                      # Outils de diagnostic
│   ├── diagnose_engines.py
│   ├── verify_dependencies.py
│   └── debug_move.py
│
├── Marlin_Config/              # ⚠️ À CRÉER - Fichiers config Marlin
│   └── (Configuration.h, etc.)
│
└── res/                        # Ressources graphiques
    ├── board.png
    └── pieces.png
```

### 3.2 Fichiers clés pour le robot

| Fichier | Description |
|---------|-------------|
| `robot_chess_controller.py` | Classe principale `ChessRobotController` - gère toute la communication avec le robot |
| `robot_calibration.py` | Script interactif pour calibrer la machine |
| `robot_config.ini` | **TOUTE LA CONFIGURATION** du robot (port série, dimensions plateau, vitesses, etc.) |
| `next_move.txt` | Fichier de communication entre l'interface et le robot |

### 3.3 Fichier de configuration `robot_config.ini`

Ce fichier est **CRITIQUE** - il contient tous les paramètres du robot :

```ini
[SERIAL]
port = COM5              # Port série (voir Gestionnaire de périphériques)
baudrate = 250000        # Vitesse de communication avec Marlin
timeout = 2

[BOARD]
square_size = 58.93      # Taille d'une case en mm
board_offset_x = 100.0   # Position X du coin a1
board_offset_y = 100.0   # Position Y du coin a1

[HEIGHTS]
z_safe = 50.0            # Hauteur de sécurité (déplacement)
z_grab = 5.0             # Hauteur pour attraper une pièce
z_lift = 30.0            # Hauteur pour soulever une pièce

[SPEEDS]
feed_rate_travel = 10000 # Vitesse de déplacement rapide (mm/min)
feed_rate_work = 1500    # Vitesse de travail (mm/min)

[GRIPPER]
gripper_type = electromagnet
grab_command = M3 S1000  # Commande pour attraper
release_command = M5     # Commande pour relâcher
grab_delay = 0.5
release_delay = 0.5

[Z_AXIS]
z_up_command = G0 Z50 F3000
z_down_command = G0 Z5 F3000
z_move_delay = 0.5

[ROBOT]
use_homing = false       # Activer/désactiver le homing automatique
```

---

## 4. Configuration Marlin (Firmware)

### 4.1 Qu'est-ce que Marlin ?

Marlin est le **firmware** qui tourne sur la carte MKS Gen V1.4. Il interprète les commandes G-code envoyées par le PC et pilote les moteurs en conséquence.

### 4.2 Installation de l'environnement

> **Note** : Un tutoriel vidéo sera créé pour cette partie.

1. **Installer Visual Studio Code** : https://code.visualstudio.com/
2. **Installer l'extension PlatformIO** :
   - Ouvrir VSCode
   - Aller dans Extensions (Ctrl+Shift+X)
   - Rechercher "PlatformIO IDE"
   - Installer

3. **Télécharger Marlin** :
   - Repo officiel : https://github.com/MarlinFirmware/Marlin
   - Télécharger la dernière version stable

### 4.3 Fichiers de configuration Marlin

⚠️ **IMPORTANT** : Les fichiers de configuration (`Configuration.h`, `Configuration_adv.h`) ne peuvent **PAS** être récupérés depuis la carte une fois uploadés. Il est **OBLIGATOIRE** de les sauvegarder dans ce repository.

**Emplacement recommandé** : `Marlin_Config/`

Les fichiers à sauvegarder :
- `Configuration.h` - Configuration principale
- `Configuration_adv.h` - Configuration avancée
- `platformio.ini` - Configuration de compilation (si modifié)

### 4.4 Paramètres Marlin importants à modifier

Voici les paramètres typiques à ajuster pour ce projet :

```cpp
// Dans Configuration.h

// Type de carte
#define MOTHERBOARD BOARD_MKS_GEN_V14

// Steps par mm (dépend de vos moteurs et courroies)
#define DEFAULT_AXIS_STEPS_PER_UNIT   { 80, 80, 400, 500 }

// Vitesses maximales
#define DEFAULT_MAX_FEEDRATE          { 300, 300, 5, 25 }

// Accélérations
#define DEFAULT_MAX_ACCELERATION      { 3000, 3000, 100, 10000 }

// Fins de course
#define USE_XMIN_PLUG
#define USE_YMIN_PLUG
// #define USE_ZMIN_PLUG  // Désactivé si pas d'endstop Z

// Baudrate (doit correspondre à robot_config.ini)
#define BAUDRATE 250000
```

### 4.5 Upload du firmware

1. Connecter la carte MKS Gen V1.4 en USB
2. Ouvrir le projet Marlin dans VSCode/PlatformIO
3. Cliquer sur "Build" pour compiler
4. Cliquer sur "Upload" pour flasher la carte

---

## 5. Calibration de la machine

### 5.1 Trouver le port série

**Windows** :
1. Ouvrir le **Gestionnaire de périphériques**
2. Développer "Ports (COM et LPT)"
3. Repérer le port de la carte (ex: `COM5`)

**Linux** :
```bash
ls /dev/ttyUSB*
# ou
ls /dev/ttyACM*
```

### 5.2 Lancer le script de calibration

```bash
cd G-Code_Controller
python robot_calibration.py
```

### 5.3 Menu de calibration

```
============================================================
MENU PRINCIPAL
============================================================
1. Test des mouvements de base
2. Test du système de préhension
3. Calibration des coins du plateau
4. Mode interactif (commandes G-code)
5. Afficher la configuration actuelle
6. Tester un coup d'échecs complet
7. Quitter
```

### 5.4 Procédure de calibration des coins

L'option **3** permet de calibrer les coins du plateau :

1. Le script vous guide pour positionner le robot au-dessus de chaque coin (a1, h1, a8, h8)
2. Utilisez les commandes :
   - `G0 X<valeur> Y<valeur>` : Déplacement
   - `+X`, `-X`, `+Y`, `-Y` : Ajustements de 1mm
   - `ok` : Valider la position
3. Le script calcule automatiquement `board_offset_x`, `board_offset_y` et `square_size`
4. Les valeurs sont sauvegardées dans `robot_config.ini`

### 5.5 Mode interactif

L'option **4** permet d'envoyer des commandes G-code directement :

**Commandes G-code utiles** :

| Commande | Description |
|----------|-------------|
| `G28` | Homing (retour origine) |
| `G28 X Y` | Homing X et Y uniquement |
| `G0 X100 Y100` | Déplacement rapide vers (100, 100) |
| `G90` | Mode absolu |
| `G91` | Mode relatif |
| `M114` | Afficher position actuelle |
| `M503` | Afficher configuration Marlin |

### 5.6 Tester un coup d'échecs

L'option **6** permet de tester un coup complet (ex: `e2e4`) :

```
[TEST D'UN COUP D'ÉCHECS COMPLET]
Entrez un coup UCI (ex: e2e4): e2e4

Déplacement: e2 (X, Y) → e4 (X, Y)
[1/9] Aller au-dessus de e2
[2/9] Z position safe
[3/9] Descendre
[4/9] Attraper la pièce
[5/9] Lever
[6/9] Se déplacer vers e4
[7/9] Descendre
[8/9] Relâcher la pièce
[9/9] Remonter
```

---

## 6. Utilisation du robot avec le jeu

### 6.1 Lancer une partie avec le robot

```bash
# Terminal 1 : Lancer l'interface graphique
python main_stockfish.py

# Terminal 2 : Lancer le contrôleur du robot
cd G-Code_Controller
python robot_chess_controller.py
```

### 6.2 Communication entre l'interface et le robot

Le fichier `next_move.txt` sert de pont entre l'interface graphique et le robot :

**Format** : `COULEUR;COUP;CAPTURE`

| Champ | Valeur | Description |
|-------|--------|-------------|
| COULEUR | `B` ou `N` | B = Blanc, N = Noir |
| COUP | `e2e4` | Format UCI (case départ + case arrivée) |
| CAPTURE | `0` ou `1` | 1 si le coup capture une pièce |

**Exemples** :
```
B;e2e4;0     # Blanc joue e2-e4, pas de capture
N;d7d5;0     # Noir joue d7-d5, pas de capture
B;e4d5;1     # Blanc joue e4xd5, capture !
```

### 6.3 Flux de jeu

```
1. Joueur humain fait son coup sur l'interface
2. L'interface écrit le coup dans next_move.txt
3. Le robot lit le fichier et exécute le coup physiquement
4. Stockfish calcule sa réponse
5. L'interface écrit le coup de Stockfish dans next_move.txt
6. Le robot exécute le coup de Stockfish
7. Retour à l'étape 1
```

---

## 7. État actuel du projet

### Ce qui fonctionne ✅

- [x] Axes X et Y fonctionnels
- [x] Déplacement des pièces sur l'échiquier
- [x] Communication PC ↔ Robot via G-code
- [x] Interface graphique Pygame
- [x] Intégration Stockfish
- [x] Gestion des captures (pièces mises sur le côté)
- [x] Script de calibration interactif
- [x] Gestion des coups spéciaux (roque, prise en passant)

### En cours de développement 🔄

- [ ] **Axe Z avec pince** : Le moteur Z n'est pas encore fixé sur la structure
- [ ] **Système de préhension** : Conception de l'attachement de la pince
- [ ] **Refonte interface** : Migration de Pygame vers Next.js/React

### À faire 📋

- [ ] Ajouter un endstop sur l'axe Z
- [ ] Fixer définitivement le moteur Z
- [ ] Concevoir et imprimer le support de pince
- [ ] Finaliser la nouvelle interface web

---

## 8. Améliorations futures

> **Note** : Cette section sera complétée au fur et à mesure de l'avancement du projet.

### Améliorations matérielles

<!-- À COMPLÉTER -->

### Améliorations logicielles

<!-- À COMPLÉTER -->

### Idées pour les prochaines itérations

<!-- À COMPLÉTER -->

---

## 9. Problèmes connus et solutions

### 9.1 Problème de précision après plusieurs coups

**Symptôme** : Après ~100 coups, le robot peut perdre en précision et ne plus cibler correctement les cases.

**Cause probable** : Accumulation d'erreurs de positionnement (jeu mécanique, glissement des courroies).

**Solutions** :
1. Effectuer un homing périodique (tous les X coups)
2. Vérifier la tension des courroies
3. Ajuster les steps/mm dans Marlin si nécessaire

### 9.2 Port série non détecté

**Solutions** :
1. Vérifier le câble USB
2. Installer les drivers CH340 (si nécessaire)
3. Vérifier dans le Gestionnaire de périphériques
4. Tester avec un autre câble USB

### 9.3 Moteur qui ne bouge pas

**Vérifications** :
1. Alimentation 20V branchée ?
2. Drivers moteur bien enfoncés sur la carte ?
3. Bonne polarité du moteur ?
4. Tester avec une commande simple : `G0 X10`

### 9.4 Le robot ne répond pas aux commandes

**Solutions** :
1. Vérifier le baudrate (250000 par défaut)
2. Attendre 2 secondes après la connexion (reset Arduino)
3. Essayer `G21` puis `G90` pour initialiser

---

## 10. Ressources et liens utiles

### Documentation technique

- [Marlin Firmware Documentation](https://marlinfw.org/docs/)
- [G-code Reference](https://marlinfw.org/meta/gcode/)
- [MKS Gen V1.4 Documentation](https://github.com/makerbase-mks/MKS-GEN)

### Bibliothèques Python utilisées

- [python-chess](https://python-chess.readthedocs.io/) - Logique d'échecs
- [pyserial](https://pyserial.readthedocs.io/) - Communication série
- [pygame](https://www.pygame.org/docs/) - Interface graphique (version actuelle)
- [stockfish](https://pypi.org/project/stockfish/) - Wrapper pour le moteur Stockfish

### Outils recommandés

- **Pronterface/Printrun** : Interface graphique pour tester les commandes G-code manuellement
- **PlatformIO** : Pour compiler et uploader Marlin

### Commandes rapides

```bash
# Installer les dépendances Python
pip install pygame python-chess pyserial stockfish requests

# Lancer l'interface de jeu
python main_stockfish.py

# Lancer la calibration du robot
cd G-Code_Controller && python robot_calibration.py

# Lancer le contrôleur du robot
cd G-Code_Controller && python robot_chess_controller.py

# Diagnostic des moteurs d'échecs
python tools/diagnose_engines.py
```

---

## Annexe : Convention des axes

```

Axe X (rangs 1→8)       
       ↑                 h8
    a8 ┼────────────────── 
       │
       │
       │     ÉCHIQUIER
       │
       │
    a1 ┼────────────────── → Axe Y (colonnes a→h)
     (0,0)              h1
     
```

- **Axe X** : Va du rang 1 au rang 8 (vertical sur le plateau)
- **Axe Y** : Va de la colonne a à la colonne h (horizontal sur le plateau)
- **Axe Z** : Hauteur (montée/descente de la pince)

---

*Document créé pour faciliter la passation du projet. N'hésitez pas à le compléter et l'améliorer !*
