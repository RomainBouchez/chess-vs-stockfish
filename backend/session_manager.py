import time
from typing import Optional


class PlayerSlot:
    """Represents one seat in a PvP game."""

    def __init__(self, sid: str, color: str):
        self.sid: str = sid
        self.color: str = color  # "white" or "black"
        self.connected: bool = True
        self.disconnect_time: Optional[float] = None
        self.ready: bool = False


class SessionManager:
    """Manages PvP sessions, queue, and disconnect timeouts alongside PvE."""

    DISCONNECT_TIMEOUT = 60  # seconds

    def __init__(self):
        # PvP player slots
        self.white_player: Optional[PlayerSlot] = None
        self.black_player: Optional[PlayerSlot] = None
        self.game_in_progress: bool = False

        # Queue: list of PlayerSlot waiting to play
        self.queue: list[PlayerSlot] = []

        # Track PvE client sids
        self.pve_sids: set[str] = set()

    # ---- Mode helpers ----

    def is_pvp_active(self) -> bool:
        """A PvP game is active if both players are assigned and game started."""
        return self.game_in_progress and self.white_player is not None and self.black_player is not None

    def get_player_color(self, sid: str) -> Optional[str]:
        if self.white_player and self.white_player.sid == sid:
            return "white"
        if self.black_player and self.black_player.sid == sid:
            return "black"
        return None

    def is_player_turn(self, sid: str, board_turn: str) -> bool:
        """Check if the given sid is allowed to move. board_turn is 'white' or 'black'."""
        color = self.get_player_color(sid)
        return color == board_turn

    def _get_slot(self, color: str) -> Optional[PlayerSlot]:
        return self.white_player if color == "white" else self.black_player

    def _set_slot(self, color: str, slot: Optional[PlayerSlot]):
        if color == "white":
            self.white_player = slot
        else:
            self.black_player = slot

    def _opponent_slot(self, color: str) -> Optional[PlayerSlot]:
        return self.black_player if color == "white" else self.white_player

    # ---- PvE ----

    def join_pve(self, sid: str):
        self.pve_sids.add(sid)

    def leave_pve(self, sid: str):
        self.pve_sids.discard(sid)

    def is_pve(self, sid: str) -> bool:
        return sid in self.pve_sids

    # ---- PvP join ----

    def join_pvp(self, sid: str, color: str) -> dict:
        """
        A player scans a QR code and joins as white or black.
        Returns a status dict: {status, position?}
        """
        if color not in ("white", "black"):
            return {"status": "error", "message": "Invalid color"}

        # Check if this is a reconnection (seat exists, disconnected, within timeout)
        existing = self._get_slot(color)
        if existing and not existing.connected and existing.disconnect_time:
            elapsed = time.time() - existing.disconnect_time
            if elapsed < self.DISCONNECT_TIMEOUT:
                # Reconnect: reassign sid
                existing.sid = sid
                existing.connected = True
                existing.disconnect_time = None
                return {"status": "reconnected"}

        # If a game is in progress, queue the player
        if self.game_in_progress:
            self.queue.append(PlayerSlot(sid, color))
            position = len(self.queue)
            return {"status": "queued", "position": position}

        # No game in progress: try to assign seat
        current = self._get_slot(color)
        if current and current.connected:
            # Seat already taken by someone else — queue
            self.queue.append(PlayerSlot(sid, color))
            position = len(self.queue)
            return {"status": "queued", "position": position}

        # Assign seat
        self._set_slot(color, PlayerSlot(sid, color))

        # Check if both seats are filled
        if self.white_player and self.black_player:
            return {"status": "ready_to_start"}

        return {"status": "waiting"}

    # ---- Ready / Start ----

    def mark_ready(self, sid: str) -> dict:
        """Mark a player as ready. Returns {can_start: bool}."""
        slot = None
        if self.white_player and self.white_player.sid == sid:
            slot = self.white_player
        elif self.black_player and self.black_player.sid == sid:
            slot = self.black_player

        if not slot:
            return {"can_start": False}

        slot.ready = True

        # Both ready?
        w_ready = self.white_player and self.white_player.ready
        b_ready = self.black_player and self.black_player.ready
        if w_ready and b_ready:
            self.game_in_progress = True
            return {"can_start": True}

        return {"can_start": False}

    # ---- Disconnect / Reconnect ----

    def handle_disconnect(self, sid: str) -> dict:
        """
        Handle a socket disconnection.
        Returns: {type: "pve"|"pvp_active"|"pvp_queue"|"none", color?, opponent_sid?}
        """
        # PvE?
        if sid in self.pve_sids:
            self.pve_sids.discard(sid)
            return {"type": "pve"}

        # Active PvP player?
        color = self.get_player_color(sid)
        if color:
            slot = self._get_slot(color)
            if slot and self.game_in_progress:
                slot.connected = False
                slot.disconnect_time = time.time()
                opponent = self._opponent_slot(color)
                return {
                    "type": "pvp_active",
                    "color": color,
                    "opponent_sid": opponent.sid if opponent else None,
                }
            else:
                # Player was in a seat but game not started — just remove
                self._set_slot(color, None)
                # Notify the other waiting player if any
                opponent = self._opponent_slot(color)
                return {
                    "type": "pvp_waiting",
                    "opponent_sid": opponent.sid if opponent else None,
                }

        # Queued player?
        for i, qs in enumerate(self.queue):
            if qs.sid == sid:
                self.queue.pop(i)
                return {"type": "pvp_queue"}

        return {"type": "none"}

    def check_timeout(self, color: str) -> bool:
        """Returns True if the player has exceeded the disconnect timeout."""
        slot = self._get_slot(color)
        if not slot or slot.connected:
            return False
        if slot.disconnect_time is None:
            return False
        return (time.time() - slot.disconnect_time) >= self.DISCONNECT_TIMEOUT

    # ---- End game ----

    def end_game(self, reason: str = "normal") -> dict:
        """
        End the current PvP game. Clear seats, promote queue.
        Returns: {promoted: [{sid, color}]}
        """
        self.game_in_progress = False
        self.white_player = None
        self.black_player = None

        # Promote queued players to seats
        promoted = []
        remaining_queue = []
        for qs in self.queue:
            current = self._get_slot(qs.color)
            if current is None:
                # Seat is free for this color
                self._set_slot(qs.color, qs)
                qs.ready = False
                promoted.append({"sid": qs.sid, "color": qs.color})
            else:
                remaining_queue.append(qs)
        self.queue = remaining_queue

        return {"promoted": promoted, "reason": reason}

    # ---- Queue helpers ----

    def get_queue_positions(self) -> list[dict]:
        """Return queue with positions for broadcasting."""
        return [{"sid": qs.sid, "position": i + 1} for i, qs in enumerate(self.queue)]

    def remove_from_queue(self, sid: str):
        self.queue = [qs for qs in self.queue if qs.sid != sid]
