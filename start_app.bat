@echo off
cd /d "%~dp0"
echo Starting Chess vs Stockfish Web App...

:: Start Backend
start "Chess Backend" cmd /k "python -m uvicorn backend.server:socket_app --host 0.0.0.0 --port 8000 --reload"

:: Start Frontend (wait a bit for backend)
timeout /t 3
cd frontend
start "Chess Frontend" cmd /k "npm run dev"

echo App is running!
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
pause
