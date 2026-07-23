"""
WebSocket Connection Manager.

Maintains a mapping of user_id → list[WebSocket] so a user can have
multiple browser tabs open simultaneously.
"""
import asyncio
import json
import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # user_id → [WebSocket, ...]
        self._connections: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self._connections[user_id].append(websocket)
        logger.debug("WS connected: user=%d  total_sockets=%d", user_id, len(self._connections[user_id]))

    def disconnect(self, websocket: WebSocket, user_id: int):
        sockets = self._connections.get(user_id, [])
        if websocket in sockets:
            sockets.remove(websocket)
        if not sockets:
            self._connections.pop(user_id, None)
        logger.debug("WS disconnected: user=%d", user_id)

    async def send_to_user(self, user_id: int, payload: dict):
        """Send a JSON payload to all open sockets for a user."""
        sockets = list(self._connections.get(user_id, []))
        dead = []
        for ws in sockets:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id)

    def is_online(self, user_id: int) -> bool:
        return bool(self._connections.get(user_id))

    def online_user_ids(self) -> List[int]:
        return list(self._connections.keys())


# Singleton — shared across the process
manager = ConnectionManager()
