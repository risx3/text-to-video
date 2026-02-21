"""WebSocket ConnectionManager — per-job broadcast with late-join state replay."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Optional

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from backend.schemas.job import WSMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # job_id → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)
        # job_id → last message sent (for late-join state replay)
        self._last_message: dict[str, WSMessage] = {}
        self._lock = asyncio.Lock()

    async def connect(self, job_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[job_id].append(ws)
        # Replay last known state to late-joining clients
        if job_id in self._last_message:
            await self._send(ws, self._last_message[job_id])
        logger.debug("WS connected for job %s (total: %d)", job_id, len(self._connections[job_id]))

    async def disconnect(self, job_id: str, ws: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(job_id, [])
            if ws in conns:
                conns.remove(ws)
        logger.debug("WS disconnected from job %s", job_id)

    async def broadcast(self, job_id: str, message: WSMessage) -> None:
        self._last_message[job_id] = message
        async with self._lock:
            sockets = list(self._connections.get(job_id, []))
        dead: list[WebSocket] = []
        for ws in sockets:
            sent = await self._send(ws, message)
            if not sent:
                dead.append(ws)
        # Clean up dead connections
        if dead:
            async with self._lock:
                for ws in dead:
                    conns = self._connections.get(job_id, [])
                    if ws in conns:
                        conns.remove(ws)

    @staticmethod
    async def _send(ws: WebSocket, message: WSMessage) -> bool:
        try:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_text(message.model_dump_json())
                return True
        except Exception as exc:
            logger.debug("WS send failed: %s", exc)
        return False


# Global singleton
manager = ConnectionManager()
