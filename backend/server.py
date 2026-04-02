import sys
import os
import asyncio
import socketio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Fix Windows asyncio subprocess bug with Python 3.8+ and Uvicorn
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add root to sys.path to allow imports if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.game_manager import GameManager
from backend.session_manager import SessionManager


class SettingsUpdate(BaseModel):
    elo: int = Field(..., ge=1350, le=3200)

class KickRequest(BaseModel):
    sid: str

class ReorderRequest(BaseModel):
    sid: str
    direction: str  # "up" or "down"

ROBOT_RETRY_INTERVAL = 10  # secondes entre chaque tentative de reconnexion

# -- Game & Session State (initialisé avant lifespan) --
game = GameManager(enable_robot=False)
session = SessionManager()

# -- Socket.IO Setup --
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')


async def _auto_connect_robot():
    """Tente de connecter le robot au démarrage, puis réessaie toutes les N secondes."""
    global game
    await asyncio.sleep(2)  # Laisser le serveur démarrer proprement
    while True:
        if game.robot is None:
            print("[AUTO-ROBOT] Tentative de connexion au robot...", flush=True)
            try:
                candidate = await asyncio.to_thread(GameManager, enable_robot=True)
                if candidate.robot is not None:
                    game = candidate
                    print("[AUTO-ROBOT] Robot connecté !", flush=True)
                    await sio.emit('robot_status', {"connected": True})
                else:
                    print(f"[AUTO-ROBOT] Échec : {candidate.robot_error}", flush=True)
                    await sio.emit('robot_status', {"connected": False, "error": candidate.robot_error})
            except Exception as e:
                print(f"[AUTO-ROBOT] Exception : {e}", flush=True)
        await asyncio.sleep(ROBOT_RETRY_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_auto_connect_robot())
    yield
    task.cancel()


# -- FastAPI Setup --
app = FastAPI(lifespan=lifespan)

# CORS: allow all origins for LAN/network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

socket_app = socketio.ASGIApp(sio, app)

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
    # Send homing command before resetting (same sequence as Home button)
    if game.robot is not None:
        success = game.robot.send_command("G28 X Y")
        if success:
            game.robot.send_command(f"G1 Z{game.robot.Z_BUMP} F{game.robot.FEED_RATE_WORK}")
    state = game.reset_game()
    await sio.emit('game_state', state)
    return state

@app.get("/api/robot/status")
def robot_status():
    return {"connected": game.robot is not None, "error": game.robot_error}

@app.post("/api/robot/home")
def robot_home():
    if game.robot is None:
        raise HTTPException(status_code=503, detail="Robot not connected")
    success = game.robot.send_command("G28 X Y")
    if success:
        # Bump Z into mechanical stop (no end-stop: motor stalls at top)
        game.robot.send_command(f"G1 Z{game.robot.Z_BUMP} F{game.robot.FEED_RATE_WORK}")
    return {"success": success}

@app.get("/api/settings")
def get_settings():
    return game.get_settings()

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    success = game.update_settings({"elo": settings.elo})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")
    return {"status": "success"}

@app.get("/api/admin/state")
def admin_get_state():
    return session.get_admin_state()

@app.post("/api/admin/kick")
async def admin_kick(request: KickRequest):
    await sio.emit('kicked', {}, to=request.sid)
    await sio.disconnect(request.sid)
    return {"status": "success", "sid": request.sid}

@app.post("/api/admin/reorder")
async def admin_reorder(request: ReorderRequest):
    if request.direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Direction must be 'up' or 'down'")
    moved = session.reorder_queue(request.sid, request.direction)
    if not moved:
        raise HTTPException(status_code=404, detail="Player not found in queue or cannot move further")
    for pos_info in session.get_queue_positions():
        await sio.emit('queue_update', {"position": pos_info["position"]}, to=pos_info["sid"])
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
        freed_color = result.get("color")
        opponent_sid = result.get("opponent_sid")

        # Try to fill the freed seat with the next queued player of that color
        promoted = session.promote_next_in_queue(freed_color) if freed_color else None

        if promoted:
            # Check if both seats are now filled → show ready screen to both
            other_slot = session._opponent_slot(promoted["color"])
            if other_slot and other_slot.connected:
                await sio.emit('pvp_status', {"status": "ready"}, to=promoted["sid"])
                await sio.emit('pvp_status', {"status": "ready"}, to=other_slot.sid)
            else:
                await sio.emit('pvp_status', {"status": "waiting"}, to=promoted["sid"])
            # Update remaining queue positions
            for pos_info in session.get_queue_positions():
                await sio.emit('queue_update', {"position": pos_info["position"]}, to=pos_info["sid"])
        else:
            # No queued player for this color — just notify opponent they're waiting again
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
        # Notify both players that homing is starting
        if session.white_player:
            await sio.emit('homing_start', {}, to=session.white_player.sid)
        if session.black_player:
            await sio.emit('homing_start', {}, to=session.black_player.sid)
        # Run G28 homing in a thread to avoid blocking the event loop
        if game.robot is not None:
            await asyncio.to_thread(game.robot.send_command, "G28 X Y")
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

    success, state, debug_log = await asyncio.to_thread(game.apply_move, move_uci)

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
                    success_ai, state_ai, debug_log_ai = await asyncio.to_thread(game.apply_move, best_move)
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
    uvicorn.run("backend.server:socket_app", host="0.0.0.0", port=8001, reload=True)
