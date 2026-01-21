# ⚡ QUICKSTART - Démarrage en 30 Secondes

Guide ultra-rapide pour lancer le projet immédiatement.

---

## 🚀 Installation Express (3 commandes)

```bash
# 1. Cloner le projet
git clone https://github.com/romainbouchez/chess-vs-stockfish.git
cd chess-vs-stockfish

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Tester l'installation
python tests/test_stockfish.py
```

**✅ Résultat attendu :** `SUCCES: Stockfish fonctionne!`

---

## 🎮 Lancer le Jeu

```bash
python main_stockfish.py
```

**C'est tout !** Le menu principal s'affiche.

---

## 📝 Premiers Pas

### Option 1 : Jouer contre l'IA (Stockfish)
1. Cliquez sur **"Play vs Stockfish"**
2. Cliquez sur **"Engines"** → Téléchargez "Stockfish latest"
3. Cliquez sur **"Play"**
4. Jouez avec la souris : cliquez sur une pièce, puis sur la destination

### Option 2 : Jouer en 1v1 (Deux écrans)
1. Cliquez sur **"Play 1v1 (2 Screens)"**
2. Deux fenêtres s'ouvrent automatiquement
3. Jouez alternativement sur chaque fenêtre

---

## ❓ Problèmes Courants

| Problème | Solution Rapide |
|----------|-----------------|
| `ModuleNotFoundError: No module named 'pygame'` | `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'requests'` | `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'serial'` | Robot uniquement : `pip install pyserial` |
| Stockfish non installé | Menu → "Engines" → Download "Stockfish latest" |
| Jeu trop lent | Settings → Réduire "Time Limit" à 0.5s |

---

## 📖 Documentation Complète

Pour plus de détails, consultez [README.md](README.md).

**Sections importantes :**
- [Structure du Projet](README.md#-structure-du-projet) - Comprendre l'organisation
- [Troubleshooting](README.md#-troubleshooting-dépannage) - Résoudre les problèmes
- [Guide Développeur](README.md#-guide-développeur) - Contribuer au projet

---

## 🎯 Fichiers Clés

| Fichier | Description |
|---------|-------------|
| `main_stockfish.py` | **🚀 POINT D'ENTRÉE** - Lancez ce fichier |
| `tests/test_stockfish.py` | Test de vérification |
| `tools/diagnose_engines.py` | Diagnostic des moteurs |
| `README.md` | Documentation complète |

---

## 🔧 Commandes Utiles

```bash
# Lancer le jeu
python main_stockfish.py

# Tester Stockfish
python tests/test_stockfish.py

# Déboguer le moteur
python tools/debug_engine.py

# Diagnostiquer les problèmes
python tools/diagnose_engines.py
```

---

**🎉 Vous êtes prêt à jouer !**

Pour toute question : bouchez@et.esiea.fr
