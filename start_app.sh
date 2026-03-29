#!/bin/bash
# Script de démarrage pour Linux / Raspberry Pi
cd "$(dirname "$0")"

echo "=== Chess vs Stockfish - Web App ==="

# Vérifier Python
if ! command -v python3 &>/dev/null; then
    echo "ERREUR: Python3 non trouvé. Installez-le avec : sudo apt install python3"
    exit 1
fi

# Vérifier Node.js
if ! command -v npm &>/dev/null; then
    echo "ERREUR: Node.js/npm non trouvé."
    echo "Installez-le avec :"
    echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    exit 1
fi

# Installer les dépendances Python si nécessaire
echo "Vérification des dépendances Python..."
pip3 install -r requirements.txt -q

# Vérifier / installer Stockfish système
if ! command -v stockfish &>/dev/null; then
    echo "Stockfish non trouvé. Installation via apt..."
    sudo apt install -y stockfish
fi

# Vérifier / initialiser Stockfish dans le projet
echo "Vérification de l'installation de Stockfish..."
python3 auto_install_stockfish.py

# Installer les dépendances frontend si nécessaire
if [ ! -d "frontend/node_modules" ]; then
    echo "Installation des dépendances frontend..."
    cd frontend && npm install && cd ..
fi

# Démarrer le backend en arrière-plan
echo "Démarrage du backend (port 8001)..."
python3 -m uvicorn backend.server:socket_app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Attendre que le backend soit prêt
sleep 3

# Démarrer le frontend en arrière-plan
echo "Démarrage du frontend (port 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=== Application démarrée ==="
echo "Frontend : http://localhost:3000"
echo "Backend  : http://localhost:8001"
echo ""
echo "Depuis un autre appareil du réseau :"
MYIP=$(hostname -I | awk '{print $1}')
echo "Frontend : http://$MYIP:3000"
echo "Backend  : http://$MYIP:8001"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter."

# Arrêter les deux processus à la sortie
trap "echo 'Arrêt...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
