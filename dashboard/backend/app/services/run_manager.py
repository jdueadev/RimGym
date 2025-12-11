"""Run manager service - orchestrates connections to multiple RimWorld instances"""

import asyncio
import logging

# Import SpectatorClient from the Python client
import sys
import time
from pathlib import Path
from typing import Dict, Optional

from app.config import settings
from app.models import RunInfo, RunStatus

# Add python client to path
python_client_path = Path(__file__).parent.parent.parent.parent.parent / "python"
sys.path.insert(0, str(python_client_path))

try:
    from client.config import ConnectionConfig
    from client.spectator_client import SpectatorClient
except ImportError:
    logging.warning("SpectatorClient not available - using mock mode")
    SpectatorClient = None
    ConnectionConfig = None

logger = logging.getLogger(__name__)


class RunManager:
    """Manages multiple training run connections"""

    def __init__(self, storage_manager) -> None:
        self.storage_manager = storage_manager
        self.runs: Dict[str, RunInfo] = {}
        self.clients: Dict[str, any] = {}  # SpectatorClient instances
        self.tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        self._stale_threshold = 30  # seconds

    async def start(self) -> None:
        """Start the run manager"""
        self._running = True
        logger.info("RunManager started")

        # Start health check task
        if settings.enable_auto_discovery:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stop the run manager and all polling tasks"""
        self._running = False

        # Cancel health check
        if hasattr(self, "_health_check_task"):
            self._health_check_task.cancel()

        # Cancel all polling tasks
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()

        # Close all clients
        for client in self.clients.values():
            try:
                if hasattr(client, "disconnect"):
                    await asyncio.get_event_loop().run_in_executor(
                        None, client.disconnect
                    )
            except Exception as e:
                logger.error(f"Error closing client: {e}")
        self.clients.clear()

        logger.info("RunManager stopped")

    async def register_run(self, run_info: RunInfo) -> str:
        """Register a new training run"""
        run_id = run_info.run_id
        self.runs[run_id] = run_info

        logger.info(f"Registered run {run_id} at {run_info.host}:{run_info.port}")

        # Create SpectatorClient if available
        if SpectatorClient and ConnectionConfig:
            try:
                config = ConnectionConfig(
                    host=run_info.host,
                    port=run_info.port,
                    timeout_ms=5000,
                    auto_reconnect=True,
                    max_reconnect_attempts=settings.max_reconnect_attempts,
                )
                client = SpectatorClient(config)

                # Connect in executor (blocking operation)
                await asyncio.get_event_loop().run_in_executor(None, client.connect)
                self.clients[run_id] = client

                logger.info(f"Connected SpectatorClient for run {run_id}")
            except Exception as e:
                logger.error(f"Failed to connect to run {run_id}: {e}")
                run_info.status = RunStatus.FAILED
                return run_id

        # Start polling task
        task = asyncio.create_task(self._poll_run(run_id))
        self.tasks[run_id] = task

        return run_id

    async def unregister_run(self, run_id: str) -> None:
        """Stop tracking a run"""
        if run_id in self.tasks:
            self.tasks[run_id].cancel()
            del self.tasks[run_id]

        if run_id in self.clients:
            client = self.clients[run_id]
            try:
                if hasattr(client, "disconnect"):
                    await asyncio.get_event_loop().run_in_executor(
                        None, client.disconnect
                    )
            except Exception as e:
                logger.error(f"Error disconnecting client for {run_id}: {e}")
            del self.clients[run_id]

        if run_id in self.runs:
            logger.info(f"Unregistered run {run_id}")
            del self.runs[run_id]

    async def list_runs(self) -> list:
        """List all registered runs"""
        return [run.model_dump() for run in self.runs.values()]

    async def get_run(self, run_id: str) -> Optional[RunInfo]:
        """Get details about a specific run"""
        return self.runs.get(run_id)

    async def _poll_run(self, run_id: str) -> None:
        """Poll a single run and push data to storage"""
        consecutive_failures = 0
        max_failures = 5
        poll_interval = settings.poll_interval_ms / 1000.0  # Convert to seconds

        while self._running and run_id in self.runs:
            try:
                run_info = self.runs[run_id]
                client = self.clients.get(run_id)

                if not client:
                    # No client available, wait and retry
                    await asyncio.sleep(poll_interval)
                    continue

                # Get state from SpectatorClient
                state = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: client.get_state(timeout_ms=1000)
                )

                if state:
                    # Transform to JSON-serializable format
                    state_dict = self._transform_state(state, run_id)

                    # Push to storage
                    await self.storage_manager.push_state(run_id, state_dict)

                    # Update run info
                    run_info.status = RunStatus.ACTIVE
                    if hasattr(state, "colonists"):
                        run_info.colonists = len(state.colonists)

                    # Reset failure counter
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1

                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Error polling run {run_id}: {e}")

                if consecutive_failures >= max_failures:
                    logger.warning(
                        f"Run {run_id} marked as STALE after {consecutive_failures} failures"
                    )
                    if run_id in self.runs:
                        self.runs[run_id].status = RunStatus.STALE

                await asyncio.sleep(poll_interval * 2)  # Back off on errors

    def _transform_state(self, state, run_id: str) -> Dict:
        """Transform protobuf state to JSON-serializable dict"""
        result = {
            "run_id": run_id,
            "timestamp": int(time.time()),
            "frame_id": getattr(state, "frame_id", 0),
            "colonists": [],
            "resources": {},
            "threats": [],
            "metrics": {},
        }

        # Transform colonists
        if hasattr(state, "colonists") and state.colonists:
            for colonist in state.colonists:
                result["colonists"].append(
                    {
                        "pawn_id": getattr(colonist, "thing_id", 0),
                        "name": getattr(colonist, "name", "Unknown"),
                        "health": getattr(colonist, "health", 0.0),
                        "mood": getattr(colonist, "mood", 0.0),
                        "job": getattr(colonist, "current_job", "Idle"),
                        "position": {
                            "x": getattr(colonist, "x", 0.0),
                            "y": getattr(colonist, "y", 0.0),
                            "z": getattr(colonist, "z", 0.0),
                        },
                    }
                )

        # Add basic metrics
        result["metrics"]["sps"] = getattr(state, "steps_per_second", 0.0)

        return result

    async def _health_check_loop(self) -> None:
        """Periodic health check for all runs"""
        while self._running:
            try:
                await asyncio.sleep(settings.health_check_interval_s)

                for run_id, run_info in list(self.runs.items()):
                    # Check if run is stale (no updates for threshold seconds)
                    # This would query Redis to check last_update timestamp
                    # For now, skip detailed health checks
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
