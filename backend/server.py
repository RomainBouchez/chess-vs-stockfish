import sys
import os
import socket
import asyncio
import socketio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add root to sys.path to allow imports if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game_manager import GameManager
from backend.session_manager import SessionManager


class SettingsUpdate(BaseModel):
    elo: int = Field(..., ge=1350, le=3200)

# -- FastAPI Setup --
app = FastAPI()

# CORS: allow localhost + LAN IP for PvP on same Wi-Fi
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    ALLOWED_ORIGINS.append(f"http://{local_ip}:3000")
    print(f"LAN access enabled: http://{local_ip}:3000")
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# -- Socket.IO Setup --
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=ALLOWED_ORIGINS)
socket_app = socketio.ASGIApp(sio, app)

# -- Game & Session State --
game = GameManager(enable_robot=False)
session = SessionManager()

# ============================================================
# REST API Endpoints
# ============================================================

@app.get("/")
def home():
    return {"status": "ok", "message": "Chess Backend Running"}

@app.post("/api/game/reset")
async def reset_game():
    # Only allow reset in PvE mode (PvP resets through session flow)
    if session.is_pvp_active():
        raise HTTPException(status_code=400, detail="Cannot reset during PvP game")
    state = game.reset_game()
    await sio.emit('game_state', state)
    return state

@app.post("/api/robot/connect")
def connect_robot():
    global game
    game = GameManager(enable_robot=True)
    return {"status": "success", "message": "Robot connection attempted"}

@app.post("/api/robot/disconnect")
def disconnect_robot():
    global game
    game.disconnect()
    game = GameManager(enable_robot=False)
    return {"status": "success", "message": "Robot disconnected"}

@app.get("/api/settings")
def get_settings():
    return game.get_settings()

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    success = game.update_settings({"elo": settings.elo})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")
    return {"status": "success"}

# ============================================================
# Socket.IO Events
# ============================================================

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Don't send game_state yet — wait for join_pve or join_pvp

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    result = session.handle_disconnect(sid)

    if result["type"] == "pvp_active":
        # Notify opponent
        opponent_sid = result.get("opponent_sid")
        if opponent_sid:
            await sio.emit('opponent_disconnected', {"timeout": SessionManager.DISCONNECT_TIMEOUT}, to=opponent_sid)
        # Start timeout task
        color = result["color"]
        asyncio.create_task(disconnect_timeout_task(color))

    elif result["type"] == "pvp_queue":
        # Update queue positions for remaining queued players
        for pos_info in session.get_queue_positions():
            await sio.emit('queue_update', {"position": pos_info["position"]}, to=pos_info["sid"])

    elif result["type"] == "pvp_waiting":
        # Player left before game started, notify opponent they're waiting again
        opponent_sid = result.get("opponent_sid")
        if opponent_sid:
            await sio.emit('pvp_status', {"status": "waiting"}, to=opponent_sid)


@sio.event
async def join_pve(sid, data=None):
    """Client declares PvE mode."""
    session.join_pve(sid)
    await sio.emit('game_state', game.get_state(), to=sid)
    print(f"Client {sid} joined as PvE")


@sio.event
async def join_pvp(sid, data):
    """Client declares PvP mode with a color."""
    color = data.get("color") if isinstance(data, dict) else None
    if color not in ("white", "black"):
        await sio.emit('pvp_error', {"message": "Invalid color"}, to=sid)
        return

    result = session.join_pvp(sid, color)
    status = result["status"]
    print(f"Client {sid} join_pvp as {color}: {status}")

    if status == "error":
        await sio.emit('pvp_error', {"message": result.get("message", "Error")}, to=sid)

    elif status == "reconnected":
        # Send current game state to reconnected player
        await sio.emit('pvp_status', {"status": "playing"}, to=sid)
        await sio.emit('game_state', game.get_state(), to=sid)
        # Notify opponent
        opponent = session._opponent_slot(color)
        if opponent and opponent.sid:
            await sio.emit('opponent_reconnected', {}, to=opponent.sid)

    elif status == "queued":
        await sio.emit('pvp_status', {"status": "queued", "position": result["position"]}, to=sid)

    elif status == "waiting":
        await sio.emit('pvp_status', {"status": "waiting"}, to=sid)

    elif status == "ready_to_start":
        # Both seats filled — tell both players they can press Ready
        await sio.emit('pvp_status', {"status": "ready"}, to=sid)
        # Also notify the other player who was waiting
        opponent = session._opponent_slot(color)
        if opponent and opponent.sid:
            await sio.emit('pvp_status', {"status": "ready"}, to=opponent.sid)


@sio.event
async def player_ready(sid, data=None):
    """Player presses the Ready button."""
    result = session.mark_ready(sid)
    if result["can_start"]:
        # Reset the board for a fresh game
        state = game.reset_game()
        # Notify both players
        if session.white_player:
            await sio.emit('game_start', {"color": "white"}, to=session.white_player.sid)
            await sio.emit('game_state', state, to=session.white_player.sid)
        if session.black_player:
            await sio.emit('game_start', {"color": "black"}, to=session.black_player.sid)
            await sio.emit('game_state', state, to=session.black_player.sid)
        print("PvP game started!")


@sio.event
async def resign(sid, data=None):
    """PvP player resigns."""
    color = session.get_player_color(sid)
    if not color or not session.is_pvp_active():
        return

    winner = "black" if color == "white" else "white"
    state = game.get_state()
    forfeit_state = {**state, "is_game_over": True, "winner": winner, "forfeit": True}

    # Send to both players
    if session.white_player:
        await sio.emit('game_state', forfeit_state, to=session.white_player.sid)
    if session.black_player:
        await sio.emit('game_state', forfeit_state, to=session.black_player.sid)

    await _end_pvp_game("resign")
    print(f"Player {color} resigned. {winner} wins.")


@sio.event
async def make_move(sid, data):
    move_uci = data.get('uci') if isinstance(data, dict) else None
    if not move_uci or not isinstance(move_uci, str):
        await sio.emit('game_state', game.get_state(), to=sid)
        return
    print(f"Received move: {move_uci}")

    # PvP mode: validate turn
    if session.is_pvp_active():
        current_turn = game.get_state()["turn"]
        if not session.is_player_turn(sid, current_turn):
            await sio.emit('game_state', game.get_state(), to=sid)
            return

    success, state, debug_log = game.apply_move(move_uci)

    # DEBUG: Emit robot debug log if any
    if debug_log:
        await sio.emit('robot_debug', {"move": move_uci, "commands": debug_log})

    if success:
        if session.is_pvp_active():
            # PvP: send to both players only, no Stockfish
            if session.white_player:
                await sio.emit('game_state', state, to=session.white_player.sid)
            if session.black_player:
                await sio.emit('game_state', state, to=session.black_player.sid)

            if state['is_game_over']:
                await _end_pvp_game("game_over")
        else:
            # PvE: existing behavior — broadcast + Stockfish auto-response
            await sio.emit('game_state', state)

            if not state['is_game_over']:
                best_move = game.get_best_move()
                if best_move:
                    print(f"Stockfish plays: {best_move}")
                    success_ai, state_ai, debug_log_ai = game.apply_move(best_move)
                    # DEBUG: Emit robot debug for Stockfish move too
                    if debug_log_ai:
                        await sio.emit('robot_debug', {"move": best_move, "commands": debug_log_ai})
                    await sio.emit('game_state', state_ai)
                else:
                    print("Stockfish has no move (Checkmate/Stalemate?)")
    else:
        await sio.emit('game_state', state, to=sid)

# ============================================================
# Helpers
# ============================================================

async def _end_pvp_game(reason: str):
    """End PvP game and notify queued players."""
    result = session.end_game(reason)
    # Notify promoted players they can press Ready
    for promoted in result.get("promoted", []):
        await sio.emit('pvp_status', {"status": "ready"}, to=promoted["sid"])
    # Update remaining queue positions
    for pos_info in session.get_queue_positions():
        await sio.emit('queue_update', {"position": pos_info["position"]}, to=pos_info["sid"])


async def disconnect_timeout_task(color: str):
    """Wait DISCONNECT_TIMEOUT seconds, then forfeit if player hasn't reconnected."""
    await asyncio.sleep(SessionManager.DISCONNECT_TIMEOUT)
    if session.check_timeout(color):
        winner = "black" if color == "white" else "white"
        state = game.get_state()
        forfeit_state = {**state, "is_game_over": True, "winner": winner, "forfeit": True}

        # Notify the opponent who is still connected
        opponent = session._opponent_slot(color)
        if opponent and opponent.connected and opponent.sid:
            await sio.emit('game_state', forfeit_state, to=opponent.sid)

        await _end_pvp_game("disconnect_forfeit")
        print(f"Player {color} timed out. {winner} wins by forfeit.")


if __name__ == "__main__":
    uvicorn.run("backend.server:socket_app", host="0.0.0.0", port=8000, reload=True)
