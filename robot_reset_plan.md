# Plan de mise en place - Reset physique de l'echiquier par le robot

## Objectif

A la fin d'une partie, le robot remet **toutes les pieces** a leur position initiale sur l'echiquier, y compris les pieces capturees stockees dans les zones de capture (graveyard).

---

## Etat actuel du systeme

### Ce qui existe deja

| Element | Fichier | Description |
|---------|---------|-------------|
| `home_robot()` | `robot_chess_controller.py:277` | Ramene le bras a l'origine (coin a1) |
| `init_board_state()` | `robot_chess_controller.py:235` | Reinitialise le dictionnaire des positions en memoire |
| `uci_to_coordinates(square)` | `robot_chess_controller.py:304` | Convertit une case UCI (ex: "e2") en coordonnees physiques (x, y) |
| `grab_piece()` / `release_piece()` | `robot_chess_controller.py` | Controle de l'electro-aimant |
| `move_to_position(x, y, z, rate)` | `robot_chess_controller.py` | Deplacement du bras vers des coordonnees |
| `move_z(z_target)` | `robot_chess_controller.py` | Controle de l'axe Z |
| `captured_pieces[]` | `robot_chess_controller.py` | Liste des pieces capturees avec `storage_pos` (x, y) |
| `board_state{}` | `robot_chess_controller.py` | Position actuelle de chaque piece sur le plateau |
| `reset_game()` | `backend/game_manager.py:130` | Reset logiciel (pas de mouvement robot) |

### Constantes physiques

```
SQUARE_SIZE     = 50.0 mm
BOARD_OFFSET_X  = 20.0 mm
BOARD_OFFSET_Y  = 20.0 mm
Z_SAFE          = 50.0 mm   (hauteur de deplacement)
Z_GRAB          = 5.0 mm    (hauteur de prise)
Z_LIFT          = 30.0 mm   (hauteur intermediaire)
GRAB_DELAY      = 0.5 s
RELEASE_DELAY   = 0.5 s
FEED_RATE_TRAVEL = 3000 mm/min
```

### Position initiale de reference

```
Rang 1 (blanc) : R  N  B  Q  K  B  N  R
Rang 2 (blanc) : P  P  P  P  P  P  P  P
Rang 3-6       : (vide)
Rang 7 (noir)  : P  P  P  P  P  P  P  P
Rang 8 (noir)  : R  N  B  Q  K  B  N  R
```

---

## Algorithme de reset

### Phase 1 - Vider le plateau (pieces mal placees)

Deplacer toutes les pieces qui ne sont **pas** a leur position initiale vers une **zone de parking temporaire** (les zones de capture gauche/droite, deja utilisees pour les graveyards).

```
Pour chaque case occupee du board_state actuel :
    Si la piece sur cette case != piece attendue en position initiale :
        Prendre la piece
        La deposer dans la zone de parking temporaire
        Mettre a jour board_state
```

> **Pourquoi cette phase ?** On ne peut pas simplement deplacer chaque piece vers sa destination, car une autre piece pourrait deja occuper cette case. Le parking temporaire evite les conflits.

### Phase 2 - Replacer les pieces capturees + parkees

Toutes les pieces hors du plateau (capturees pendant la partie + parkees en phase 1) doivent etre replacees.

```
Pour chaque piece a replacer (parking + captured_pieces[]) :
    Calculer sa case de destination initiale
    Prendre la piece a sa position de stockage
    La deposer sur sa case initiale
    Mettre a jour board_state
```

### Phase 3 - Deplacer les pieces deja bien placees (skip)

Les pieces qui etaient deja a leur position initiale n'ont pas besoin d'etre deplacees. On les ignore.

### Phase 4 - Finalisation

```
1. home_robot()         -> ramener le bras a l'origine
2. init_board_state()   -> reinitialiser le tracking en memoire
3. Vider captured_pieces[] et reset des compteurs de capture
4. Sauvegarder l'etat dans robot_state.json
```

---

## Gestion de l'identification des pieces

### Probleme

Le robot ne peut pas **identifier visuellement** quelle piece se trouve sur quelle case. Il se base uniquement sur `board_state{}` (tracking logiciel des mouvements).

### Contrainte

L'algorithme depend de la fiabilite du `board_state`. Si un mouvement a ete mal track (piece deplacee a la main par l'humain), le robot ne saura pas ou sont les pieces reellement.

### Solution pragmatique

On fait confiance au `board_state` et a `captured_pieces[]` qui sont mis a jour a chaque coup. En cas de desynchronisation, l'utilisateur doit replacer les pieces manuellement.

---

## Zone de parking temporaire

Reutiliser les zones de capture (graveyard) existantes comme parking :

```
Cote gauche du plateau : Y = BOARD_OFFSET_Y - CAPTURE_SPACING
Cote droit du plateau  : Y = BOARD_OFFSET_Y + (8 * SQUARE_SIZE) + CAPTURE_SPACING

Organisation en matrice 2x8 de chaque cote (16 slots par cote = 32 max)
```

Les slots de parking sont calcules avec `get_capture_zone_position()` existante, en utilisant un compteur temporaire.

---

## Implementation technique

### Nouvelle methode : `reset_board()`

Fichier : `G-Code_Controller/robot_chess_controller.py`

```python
def reset_board(self):
    """Remet physiquement toutes les pieces a leur position initiale."""

    INITIAL_BOARD = {
        "a1": {"color": "white", "type": "rook"},
        "b1": {"color": "white", "type": "knight"},
        "c1": {"color": "white", "type": "bishop"},
        "d1": {"color": "white", "type": "queen"},
        "e1": {"color": "white", "type": "king"},
        "f1": {"color": "white", "type": "bishop"},
        "g1": {"color": "white", "type": "knight"},
        "h1": {"color": "white", "type": "rook"},
        "a2": {"color": "white", "type": "pawn"},
        "b2": {"color": "white", "type": "pawn"},
        "c2": {"color": "white", "type": "pawn"},
        "d2": {"color": "white", "type": "pawn"},
        "e2": {"color": "white", "type": "pawn"},
        "f2": {"color": "white", "type": "pawn"},
        "g2": {"color": "white", "type": "pawn"},
        "h2": {"color": "white", "type": "pawn"},
        "a7": {"color": "black", "type": "pawn"},
        "b7": {"color": "black", "type": "pawn"},
        "c7": {"color": "black", "type": "pawn"},
        "d7": {"color": "black", "type": "pawn"},
        "e7": {"color": "black", "type": "pawn"},
        "f7": {"color": "black", "type": "pawn"},
        "g7": {"color": "black", "type": "pawn"},
        "h7": {"color": "black", "type": "pawn"},
        "a8": {"color": "black", "type": "rook"},
        "b8": {"color": "black", "type": "knight"},
        "c8": {"color": "black", "type": "bishop"},
        "d8": {"color": "black", "type": "queen"},
        "e8": {"color": "black", "type": "king"},
        "f8": {"color": "black", "type": "bishop"},
        "g8": {"color": "black", "type": "knight"},
        "h8": {"color": "black", "type": "rook"},
    }

    # --- Phase 1 : identifier les pieces a deplacer ---
    pieces_to_park = []    # pieces sur le plateau mais mal placees
    already_correct = set() # cases deja correctes

    for square, piece in list(self.board_state.items()):
        expected = INITIAL_BOARD.get(square)
        if expected and expected["type"] == piece["type"] and expected["color"] == piece["color"]:
            already_correct.add(square)
        else:
            pieces_to_park.append({"square": square, **piece})

    # --- Phase 2 : parker les pieces mal placees ---
    parked_pieces = []  # {"piece": {...}, "storage_pos": (x, y)}
    park_counter = 0

    for piece_info in pieces_to_park:
        source = self.uci_to_coordinates(piece_info["square"])
        park_pos = self._get_temp_parking_position(park_counter)

        self._pick_and_place(source, park_pos)

        parked_pieces.append({
            "type": piece_info["type"],
            "color": piece_info["color"],
            "storage_pos": park_pos,
        })
        del self.board_state[piece_info["square"]]
        park_counter += 1

    # --- Phase 3 : rassembler toutes les pieces a replacer ---
    all_pieces_to_place = []

    # Pieces parkees temporairement
    for p in parked_pieces:
        all_pieces_to_place.append(p)

    # Pieces capturees (dans les graveyards)
    for p in self.captured_pieces:
        all_pieces_to_place.append(p)

    # --- Phase 4 : replacer chaque piece a sa position initiale ---
    placed_squares = set(already_correct)

    for target_square, expected_piece in INITIAL_BOARD.items():
        if target_square in placed_squares:
            continue

        # Chercher la piece correspondante dans les pieces disponibles
        match = None
        for i, p in enumerate(all_pieces_to_place):
            if p["type"] == expected_piece["type"] and p["color"] == expected_piece["color"]:
                match = (i, p)
                break

        if match:
            idx, piece = match
            source_pos = piece["storage_pos"]
            dest_pos = self.uci_to_coordinates(target_square)

            self._pick_and_place(source_pos, dest_pos)

            all_pieces_to_place.pop(idx)
            placed_squares.add(target_square)

    # --- Phase 5 : finalisation ---
    self.home_robot()
    self.init_board_state()
    self.captured_pieces.clear()
    self.white_capture_count = 0
    self.black_capture_count = 0
    self.save_state()
```

### Methode utilitaire : `_pick_and_place()`

Extraire la sequence de pick-and-place existante en methode reutilisable :

```python
def _pick_and_place(self, source_pos, dest_pos):
    """Deplace une piece de source_pos (x,y) vers dest_pos (x,y)."""
    sx, sy = source_pos
    dx, dy = dest_pos

    # Aller au dessus de la piece source
    self.move_to_position(sx, sy, self.Z_SAFE, self.FEED_RATE_TRAVEL)
    # Descendre pour attraper
    self.move_z(self.Z_GRAB)
    self.grab_piece()
    # Lever la piece
    self.move_z(self.Z_LIFT)
    # Deplacer vers destination
    self.move_to_position(dx, dy, self.Z_LIFT, self.FEED_RATE_TRAVEL)
    # Descendre pour poser
    self.move_z(self.Z_GRAB)
    self.release_piece()
    # Remonter
    self.move_z(self.Z_SAFE)
```

### Methode utilitaire : `_get_temp_parking_position()`

```python
def _get_temp_parking_position(self, index):
    """Calcule la position de parking temporaire pour une piece."""
    board_size = 8 * self.SQUARE_SIZE
    spacing = self.CAPTURE_SPACING

    # Utiliser cote gauche (index 0-15) puis cote droit (index 16-31)
    if index < 16:
        side_index = index
        base_y = self.BOARD_OFFSET_Y - spacing
    else:
        side_index = index - 16
        base_y = self.BOARD_OFFSET_Y + board_size + spacing

    col = side_index % 2
    row = side_index // 2

    x = self.BOARD_OFFSET_X + (row * self.SQUARE_SIZE) + (self.SQUARE_SIZE / 2)
    y = base_y - (col * spacing) if index < 16 else base_y + (col * spacing)

    return (x, y)
```

---

## Integration backend

### Fichier : `backend/game_manager.py`

Ajouter l'appel dans `reset_game()` :

```python
def reset_game(self):
    self.board = chess.Board()
    self.captured_white.clear()
    self.captured_black.clear()

    # Reset physique par le robot
    if self.robot and self.robot.connected:
        self.robot.reset_board()

    self.save_state()
```

### Fichier : `backend/server.py`

Ajouter un endpoint dedie (le reset robot est lent, il faut un endpoint async) :

```python
@app.route('/api/game/reset-board', methods=['POST'])
def reset_board():
    """Lance le reset physique du plateau par le robot."""
    if not game.robot or not game.robot.connected:
        return jsonify({"error": "Robot non connecte"}), 400

    # Lancer en thread pour ne pas bloquer le serveur
    import threading
    thread = threading.Thread(target=game.robot.reset_board)
    thread.start()

    return jsonify({"status": "reset_started"})

# Endpoint pour verifier l'avancement
@app.route('/api/game/reset-board/status', methods=['GET'])
def reset_board_status():
    return jsonify({"in_progress": game.robot.is_resetting})
```

### Fichier : `frontend/app/page.tsx`

Ajouter un bouton dans le modal de fin de partie :

```tsx
const handleResetBoard = async () => {
  setIsResetting(true);
  try {
    await fetch('/api/game/reset-board', { method: 'POST' });
    // Polling du statut jusqu'a completion
    const poll = setInterval(async () => {
      const res = await fetch('/api/game/reset-board/status');
      const data = await res.json();
      if (!data.in_progress) {
        clearInterval(poll);
        setIsResetting(false);
        handleReset(); // reset logiciel apres
      }
    }, 2000);
  } catch (err) {
    setIsResetting(false);
  }
};
```

---

## Estimation du temps de reset

| Parametre | Valeur |
|-----------|--------|
| Pieces a deplacer (pire cas) | 32 (16 parkees + 16 capturees) |
| Temps moyen par pick-and-place | ~8-10 secondes |
| Temps total estime (pire cas) | ~4-5 minutes |
| Temps moyen (partie typique) | ~2-3 minutes |

---

## Optimisations possibles (v2)

1. **Tri par proximite** : Ordonner les pieces a replacer pour minimiser la distance de deplacement du bras (algorithme du plus proche voisin).
2. **Skip des pieces deja correctes** : Deja implemente dans l'algorithme (via `already_correct`).
3. **Pieces promues** : Gerer le cas ou un pion a ete promu (la piece physique reste un pion, seul le tracking change). Lors du reset, remettre le pion a sa case initiale.
4. **Parallelisme Phase 1/2** : Si une piece parkee doit aller a une case qui est deja libre, on peut la placer directement sans la parker (optimisation "placement direct").

---

## Cas limites a gerer

| Cas | Comportement |
|-----|-------------|
| Piece promue (pion devenu dame) | Le pion physique est remis a sa case initiale de pion |
| Deux pions du meme type a distinguer | N'importe quel pion de la bonne couleur convient |
| `board_state` desynchronise | Le robot suit son tracking, l'utilisateur doit corriger manuellement |
| Robot deconnecte en plein reset | Sauvegarder l'etat apres chaque mouvement pour reprendre |
| Partie abandonnee (peu de mouvements) | Peu de pieces a deplacer, reset rapide |

---

## Fichiers a modifier

| Fichier | Modification |
|---------|-------------|
| `G-Code_Controller/robot_chess_controller.py` | Ajouter `reset_board()`, `_pick_and_place()`, `_get_temp_parking_position()`, flag `is_resetting` |
| `backend/game_manager.py` | Appeler `robot.reset_board()` dans `reset_game()` |
| `backend/server.py` | Ajouter endpoints `/api/game/reset-board` et `/api/game/reset-board/status` |
| `frontend/app/page.tsx` | Ajouter bouton "Reset plateau" + logique de polling |
