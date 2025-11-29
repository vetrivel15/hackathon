from __future__ import annotations

import asyncio
import json
import logging
from typing import Set, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts to clients."""

    def __init__(self) -> None:
        self._active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self._active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self._active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all connected clients.

        Args:
            message: Dictionary to send as JSON
        """
        if not self._active_connections:
            return

        message_str = json.dumps(message)
        disconnected = set()

        async with self._lock:
            connections = list(self._active_connections)

        for websocket in connections:
            try:
                await websocket.send_text(message_str)
            except WebSocketDisconnect:
                disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                self._active_connections -= disconnected
            logger.info(f"Cleaned up {len(disconnected)} disconnected clients")

    async def broadcast_telemetry(self, robot_id: str, telemetry: Dict[str, Any]) -> None:
        """Broadcast robot telemetry update to all clients."""
        message = {
            "type": "telemetry",
            "robot_id": robot_id,
            "data": telemetry,
        }
        await self.broadcast(message)

    async def broadcast_pose(self, robot_id: str, pose: Dict[str, float]) -> None:
        """Broadcast robot pose update to all clients."""
        message = {
            "type": "pose",
            "robot_id": robot_id,
            "data": pose,
        }
        await self.broadcast(message)

    async def broadcast_status(self, robot_id: str, status: str) -> None:
        """Broadcast robot status change to all clients."""
        message = {
            "type": "status",
            "robot_id": robot_id,
            "status": status,
        }
        await self.broadcast(message)

    async def broadcast_error(self, robot_id: str, error: Dict[str, Any]) -> None:
        """Broadcast robot error to all clients."""
        message = {
            "type": "error",
            "robot_id": robot_id,
            "error": error,
        }
        await self.broadcast(message)

    async def broadcast_joints(self, robot_id: str, joints_data: Dict[str, Any]) -> None:
        """Broadcast robot joints update to all clients."""
        message = {
            "type": "joints",
            "robot_id": robot_id,
            "data": joints_data,
        }
        await self.broadcast(message)

    async def broadcast_gps(self, robot_id: str, gps_data: Dict[str, Any]) -> None:
        """Broadcast robot GPS update to all clients."""
        message = {
            "type": "gps",
            "robot_id": robot_id,
            "data": gps_data,
        }
        await self.broadcast(message)

    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Send message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._active_connections)


# Global instance
ws_manager = WebSocketManager()
