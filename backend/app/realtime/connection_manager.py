import json
import logging
from collections import deque
from typing import List, Dict, Any, Optional, Tuple
from fastapi import WebSocket, WebSocketDisconnect
from app.realtime.events import build_event_envelope
from app.utils import now_utc

logger = logging.getLogger("dlas.realtime")


class ConnectionManager:
    def __init__(self, buffer_size: int = 1000):
        # Maps active WebSocket instance to authenticated user metadata
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        # In-memory circular buffer for missed-event replay
        self.event_buffer: deque = deque(maxlen=buffer_size)
        self.latest_seq: int = 0

    async def connect(self, websocket: WebSocket, user: Optional[Dict[str, Any]] = None):
        await websocket.accept()
        self.active_connections[websocket] = user or {
            "user_id": None,
            "role": "anonymous",
            "connected_at": now_utc().isoformat(),
        }
        user_info = f"{user.get('email', 'unknown')} ({user.get('role', 'unknown')})" if user else "anonymous"
        logger.info(f"WebSocket client connected [{user_info}]. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            user = self.active_connections.pop(websocket)
            logger.info(f"WebSocket client disconnected [{user.get('email', 'unknown')}]. Active connections: {len(self.active_connections)}")

    def get_latest_seq(self) -> int:
        return self.latest_seq

    def clear_buffer(self):
        """Used in test fixtures to reset buffer state."""
        self.event_buffer.clear()
        self.latest_seq = 0

    def get_events_since(self, since_seq: int) -> Tuple[List[Dict[str, Any]], bool, int]:
        """
        Retrieve buffered events that occurred strictly after `since_seq`.
        Returns:
            (events_list, reset_required, latest_seq)
        If since_seq is older than the oldest event in the buffer (and buffer has reached capacity),
        reset_required is True, meaning the client must perform a full authoritative server refresh.
        """
        latest = self.latest_seq

        if not self.event_buffer:
            return ([], False, latest)

        earliest_seq = self.event_buffer[0].get("seq", 0)

        # If client is requesting sequence older than what's retained in full buffer
        if since_seq < earliest_seq and len(self.event_buffer) == self.event_buffer.maxlen:
            return ([], True, latest)

        # Filter events where seq > since_seq
        missed = [e for e in self.event_buffer if e.get("seq", 0) > since_seq]
        return (missed, False, latest)

    async def broadcast_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        actor: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds standardized envelope, records into in-memory ring buffer,
        and broadcasts to all connected clients.
        """
        envelope = build_event_envelope(event_type, payload, actor)
        self.latest_seq = envelope["seq"]
        self.event_buffer.append(envelope)

        await self.broadcast_raw(envelope)
        return envelope

    async def broadcast_raw(self, message: Dict[str, Any]):
        data_text = json.dumps(message, default=str)
        dead_connections: List[WebSocket] = []

        for connection in list(self.active_connections.keys()):
            try:
                await connection.send_text(data_text)
            except Exception as e:
                logger.warning(f"Error sending message to WebSocket client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


manager = ConnectionManager()
