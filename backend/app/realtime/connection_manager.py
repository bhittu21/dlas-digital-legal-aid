import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.realtime.events import build_event_envelope

logger = logging.getLogger("dlas.realtime")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        actor: Optional[Dict[str, Any]] = None
    ):
        envelope = build_event_envelope(event_type, payload, actor)
        await self.broadcast_raw(envelope)

    async def broadcast_raw(self, message: Dict[str, Any]):
        data_text = json.dumps(message, default=str)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data_text)
            except Exception as e:
                logger.warning(f"Error sending message to WebSocket client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


manager = ConnectionManager()
