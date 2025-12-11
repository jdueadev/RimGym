"""WebSocket endpoints for real-time updates"""

import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self) -> None:
        # run_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> run_id
        self.connection_runs: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, run_id: str) -> None:
        """Accept and register a new connection"""
        await websocket.accept()

        if run_id not in self.active_connections:
            self.active_connections[run_id] = set()

        self.active_connections[run_id].add(websocket)
        self.connection_runs[websocket] = run_id

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a connection"""
        run_id = self.connection_runs.get(websocket)
        if run_id and run_id in self.active_connections:
            self.active_connections[run_id].discard(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]

        if websocket in self.connection_runs:
            del self.connection_runs[websocket]

    async def broadcast(self, run_id: str, message: dict) -> None:
        """Broadcast message to all clients subscribed to a run"""
        if run_id not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[run_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/runs/{run_id}/state")
async def websocket_run_state(websocket: WebSocket, run_id: str) -> None:
    """WebSocket endpoint for real-time run state updates"""
    await manager.connect(websocket, run_id)

    # Send welcome message
    await websocket.send_json(
        {
            "type": "connected",
            "run_id": run_id,
            "timestamp": int(asyncio.get_event_loop().time()),
            "update_rate_hz": 2,
        }
    )

    try:
        while True:
            # Receive messages from client (e.g., heartbeat acks)
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "heartbeat_ack":
                # Client acknowledged heartbeat
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/runs/all")
async def websocket_all_runs(websocket: WebSocket) -> None:
    """WebSocket endpoint for aggregate run updates"""
    await websocket.accept()

    try:
        while True:
            # TODO: Implement aggregate updates
            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        pass
