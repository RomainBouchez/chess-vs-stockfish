# Modifications de l'axe Z - Passage aux commandes M280

## Résumé des changements

L'axe Z du robot a été modifié pour utiliser des commandes servo (M280) au lieu des commandes de mouvement linéaire standard (G0/G1 Z).

## Nouvelles commandes

- **Montée de l'axe Z** : `M280 P0 S12`
- **Descente de l'axe Z** : `M280 P0 S168`

## Fichiers modifiés

### 1. `robot_config.ini`
- **Ajout** : Nouvelle section `[Z_AXIS]` avec les paramètres :
  - `z_up_command = M280 P0 S12`
  - `z_down_command = M280 P0 S168`
  - `z_move_delay = 0.5`

### 2. `robot_chess_controller.py`
- **Ajout** : Chargement des commandes Z dans `load_config()`
- **Ajout** : Nouvelle fonction `move_z(z_target)` qui choisit automatiquement UP ou DOWN selon la hauteur cible
- **Modification** : `move_to_position()` maintenant :
  - Utilise `G0` pour les axes X et Y uniquement
  - Appelle `move_z()` pour gérer l'axe Z avec M280

### 3. `robot_calibration.py`
- **Ajout** : Fonction `load_z_commands()` pour charger les paramètres Z
- **Ajout** : Fonction `get_z_command(z_target)` qui retourne la commande M280 appropriée
- **Modification** : `test_movement()` - sépare les mouvements XY et Z
- **Modification** : `test_chess_move()` - utilise les commandes M280 pour l'axe Z
- **Modification** : `show_gcode_help()` - mise à jour de la documentation

### 4. `test_z_commands.py` (nouveau)
- Script de test pour vérifier la configuration et les imports

## Logique de fonctionnement

Le système détermine automatiquement quelle commande M280 utiliser en comparant la hauteur cible avec `Z_GRAB` :

```python
if z_target <= Z_GRAB:
    # Position basse -> Descendre
    commande = M280 P0 S168
else:
    # Position haute -> Monter
    commande = M280 P0 S12
```

## Hauteurs de référence (robot_config.ini)

- `z_safe = 50.0` → Position de sécurité (UP)
- `z_grab = 5.0` → Position de préhension (DOWN)
- `z_lift = 30.0` → Position de transport (UP)

## Test de la configuration

Pour vérifier que tout fonctionne :

```bash
cd "G-Code_Controller"
python test_z_commands.py
```

## Utilisation en mode interactif

1. Lancer le script de calibration :
```bash
python robot_calibration.py
```

2. Choisir l'option "4. Mode interactif"

3. Tester les commandes manuellement :
```
G-code> M280 P0 S12    # Monter
G-code> M280 P0 S168   # Descendre
```

## Avantages

- ✅ Séparation claire entre mouvements XY (linéaires) et Z (servo)
- ✅ Configuration centralisée dans `robot_config.ini`
- ✅ Compatibilité maintenue avec l'ancien code
- ✅ Gestion automatique UP/DOWN selon la hauteur
- ✅ Délai configurable pour les mouvements Z

## Notes importantes

- Les axes X et Y continuent d'utiliser `G0`/`G1` (mouvement linéaire)
- Seul l'axe Z utilise maintenant `M280` (servo)
- Le délai `z_move_delay` permet au servo d'atteindre sa position avant la prochaine commande
- Les valeurs S12 et S168 peuvent être ajustées dans `robot_config.ini` si nécessaire
