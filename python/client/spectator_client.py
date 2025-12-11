"""
SpectatorClient - Main orchestrator for RimWorld ML Bridge client.

Manages connection, threads, and provides high-level API for RL agents.
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from .actor import ActorThread
from .connection import ConnectionManager
from .inference import InferenceThread
from .listener import EventDetectionConfig, ListenerThread
from .queues import ActionQueue, EventQueue, StateQueue

logger = logging.getLogger(__name__)


class ClientState(Enum):
    """Client lifecycle states."""

    INITIALIZED = "initialized"
    CONNECTING = "connecting"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ClientConfig:
    """Configuration for SpectatorClient."""

    # Connection
    host: str = "localhost"
    port: int = 50051
    connect_timeout: float = 10.0
    reconnect_attempts: int = 10
    reconnect_backoff: float = 1.0

    # Operating Mode
    training_mode: bool = False
    inference_mode: bool = True

    # Listener
    poll_interval_ms: int = 100
    max_state_queue_size: int = 10
    health_check_interval_ms: int = 5000

    # Inference
    max_inference_latency_ms: int = 100
    executive_policy: Optional[Any] = None

    # Actor
    max_reflex_latency_ms: int = 10
    max_event_queue_size: int = 100
    reflex_policy: Optional[Any] = None

    # Logging
    log_level: str = "INFO"
    metrics_enabled: bool = True
    metrics_interval_ms: int = 1000

    def __post_init__(self):
        """Validate configuration."""
        if self.training_mode and self.inference_mode:
            logger.warning(
                "Both training_mode and inference_mode enabled. Using training_mode."
            )
            self.inference_mode = False

        if not self.training_mode and not self.inference_mode:
            logger.warning("Neither mode enabled. Defaulting to inference_mode.")
            self.inference_mode = True


class SpectatorClient:
    """
    Main client orchestrating all threads for RimWorld ML Bridge.

    Manages:
    - Connection to RimWorld server
    - Listener thread (state polling)
    - Inference thread (Executive policy) - Phase IV.3
    - Actor thread (Reflex policy) - Phase IV.4
    - Shared queues and synchronization

    Usage:
        client = SpectatorClient(ClientConfig(...))
        client.start()
        client.wait_ready(timeout=30.0)

        # Use client...
        state = client.get_state()

        client.stop()
    """

    def __init__(self, config: ClientConfig):
        """
        Initialize SpectatorClient.

        Args:
            config: Client configuration
        """
        self.config = config
        self._state = ClientState.INITIALIZED

        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.log_level.upper()),
            format="[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s",
        )

        # Connection manager
        self.connection = ConnectionManager(
            host=config.host,
            port=config.port,
            connect_timeout=config.connect_timeout,
            reconnect_attempts=config.reconnect_attempts,
            reconnect_backoff=config.reconnect_backoff,
        )

        # Shared queues
        self.state_queue = StateQueue(maxsize=config.max_state_queue_size)
        self.event_queue = EventQueue(maxsize=config.max_event_queue_size)
        self.action_queue = ActionQueue(maxsize=100)

        # Thread references (will be created in start())
        self._listener_thread: Optional[threading.Thread] = None
        self._inference_thread: Optional[threading.Thread] = None
        self._actor_thread: Optional[threading.Thread] = None
        self._metrics_thread: Optional[threading.Thread] = None

        # Synchronization
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._state_lock = threading.Lock()

        # Metrics
        self._metrics = {
            "states_received": 0,
            "events_detected": 0,
            "actions_sent": 0,
            "connection_errors": 0,
            "last_state_time": 0.0,
        }
        self._metrics_lock = threading.Lock()

        logger.info(
            f"SpectatorClient initialized (mode={'training' if config.training_mode else 'inference'})"
        )

    def start(self) -> None:
        """
        Start all threads and establish connection.

        Raises:
            RuntimeError: If already started or failed to connect
        """
        with self._state_lock:
            if self._state != ClientState.INITIALIZED:
                raise RuntimeError(f"Cannot start from state: {self._state}")

            self._state = ClientState.CONNECTING

        logger.info("Starting SpectatorClient...")

        # Connect to server
        if not self.connection.connect():
            with self._state_lock:
                self._state = ClientState.ERROR
            raise RuntimeError("Failed to connect to RimWorld server")

        # Start threads
        self._start_threads()

        with self._state_lock:
            self._state = ClientState.RUNNING

        logger.info("SpectatorClient started successfully")

    def _start_threads(self) -> None:
        """Start all worker threads."""

        # Start Listener thread (Phase IV.2)
        event_config = EventDetectionConfig()
        self._listener_thread = ListenerThread(
            connection_manager=self.connection,
            state_queue=self.state_queue,
            event_queue=self.event_queue,
            stop_event=self._stop_event,
            poll_interval_ms=self.config.poll_interval_ms,
            health_check_interval_ms=self.config.health_check_interval_ms,
            event_config=event_config,
            metrics_collector=self._metrics_collector
            if hasattr(self, "_metrics_collector")
            else None,
        )
        self._listener_thread.start()
        logger.info("Listener thread started")

        # Start Inference thread (Phase IV.3)
        if self.config.executive_policy:
            self._inference_thread = InferenceThread(
                policy=self.config.executive_policy,
                state_queue=self.state_queue,
                action_queue=self.action_queue,
                stop_event=self._stop_event,
                timeout_ms=self.config.max_inference_latency_ms,
                metrics_collector=None,  # TODO: Add metrics collector
            )
            self._inference_thread.start()
            logger.info("Inference thread started")
        else:
            logger.warning("No executive_policy configured, skipping Inference thread")

        # Start Actor thread (Phase IV.4)
        if self.config.reflex_policy:
            self._actor_thread = ActorThread(
                policy=self.config.reflex_policy,
                event_queue=self.event_queue,
                action_queue=self.action_queue,
                stop_event=self._stop_event,
                timeout_ms=50,  # 50ms timeout for event queue
                metrics_collector=None,  # TODO: Add metrics collector
            )
            self._actor_thread.start()
            logger.info("Actor thread started")
        else:
            logger.warning("No reflex_policy configured, skipping Actor thread")

        # Start metrics thread if enabled
        if self.config.metrics_enabled:
            self._metrics_thread = threading.Thread(
                target=self._metrics_loop, name="MetricsThread", daemon=True
            )
            self._metrics_thread.start()

        # Signal ready
        self._ready_event.set()

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop all threads and disconnect gracefully.

        Args:
            timeout: Timeout for thread joins in seconds
        """
        with self._state_lock:
            if self._state in (ClientState.STOPPED, ClientState.STOPPING):
                logger.warning(f"Already stopping/stopped: {self._state}")
                return

            self._state = ClientState.STOPPING

        logger.info("Stopping SpectatorClient...")

        # Signal all threads to stop
        self._stop_event.set()

        # Wait for threads to finish
        threads = [
            self._listener_thread,
            self._inference_thread,
            self._actor_thread,
            self._metrics_thread,
        ]

        for thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=timeout)
                if thread.is_alive():
                    logger.warning(f"Thread {thread.name} did not stop within timeout")

        # Disconnect
        self.connection.disconnect()

        with self._state_lock:
            self._state = ClientState.STOPPED

        logger.info("SpectatorClient stopped")

    def wait_ready(self, timeout: float = 30.0) -> bool:
        """
        Wait for client to be ready.

        Args:
            timeout: Timeout in seconds

        Returns:
            True if ready, False on timeout
        """
        ready = self._ready_event.wait(timeout=timeout)

        if ready:
            logger.info("SpectatorClient is ready")
        else:
            logger.error(f"SpectatorClient not ready after {timeout}s")

        return ready

    def get_state(self, timeout: Optional[float] = 1.0) -> Optional[Any]:
        """
        Get latest state from state queue (non-blocking).

        Args:
            timeout: Timeout in seconds

        Returns:
            RichGameState object with Phase V data, or None
        """
        # Import here to avoid circular dependency
        from .parsers import parse_rich_state_message

        proto_state = self.state_queue.get_latest()
        if proto_state:
            # Parse protobuf to RichGameState
            return parse_rich_state_message(proto_state)
        return None

    def send_action(self, action: Any) -> bool:
        """
        Send action to action queue for execution.

        Args:
            action: Action object

        Returns:
            True if queued successfully, False otherwise
        """
        return self.action_queue.put(action)

    def get_metrics(self) -> dict:
        """
        Get current metrics snapshot.

        Returns:
            Dictionary of metrics
        """
        with self._metrics_lock:
            return self._metrics.copy()

    def is_running(self) -> bool:
        """Check if client is running."""
        with self._state_lock:
            return self._state == ClientState.RUNNING

    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self.connection.is_connected()

    def _metrics_loop(self) -> None:
        """Background metrics collection loop."""
        logger.info("Metrics thread started")

        interval = self.config.metrics_interval_ms / 1000.0

        while not self._stop_event.is_set():
            time.sleep(interval)

            # Collect metrics
            with self._metrics_lock:
                metrics = self._metrics.copy()

            # Log metrics
            logger.info(
                f"Metrics: states={metrics['states_received']}, "
                f"events={metrics['events_detected']}, "
                f"actions={metrics['actions_sent']}, "
                f"errors={metrics['connection_errors']}, "
                f"queues=(state:{self.state_queue.qsize()}, "
                f"event:{self.event_queue.qsize()}, "
                f"action:{self.action_queue.qsize()})"
            )

        logger.info("Metrics thread stopped")

    def _update_metric(self, key: str, value: Any) -> None:
        """Thread-safe metric update."""
        with self._metrics_lock:
            self._metrics[key] = value

    def _increment_metric(self, key: str, delta: int = 1) -> None:
        """Thread-safe metric increment."""
        with self._metrics_lock:
            self._metrics[key] = self._metrics.get(key, 0) + delta

    def __enter__(self):
        """Context manager entry."""
        self.start()
        self.wait_ready()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
