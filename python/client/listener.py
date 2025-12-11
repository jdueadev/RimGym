"""
Listener Thread - Async state polling and event detection.

Continuously polls RimWorld server for state updates and detects events.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from mlbridge_pb2 import CommandMessage, CommandType, StateMessage

from .queues import EventPriority, EventQueue, StateQueue

logger = logging.getLogger(__name__)


@dataclass
class EventDetectionConfig:
    """Configuration for event detection."""

    # Health thresholds
    health_critical_threshold: float = 0.2  # <20% health = CRITICAL
    health_warning_threshold: float = 0.5  # <50% health = HIGH

    # Movement detection
    movement_threshold: float = 0.5  # Units/sec to consider "moving"

    # Job changes
    detect_job_changes: bool = True

    # Colonist lifecycle
    detect_new_colonists: bool = True
    detect_dead_colonists: bool = True


class ListenerThread(threading.Thread):
    """
    Listener thread that polls RimWorld server for state updates.

    Responsibilities:
    - Poll server at configurable interval
    - Deserialize protobuf state messages
    - Detect events via state diffing
    - Push states to StateQueue
    - Push events to EventQueue
    - Monitor connection health

    Thread-safe and designed for long-running operation.
    """

    def __init__(
        self,
        connection_manager,
        state_queue: StateQueue,
        event_queue: EventQueue,
        stop_event: threading.Event,
        poll_interval_ms: int = 100,
        health_check_interval_ms: int = 5000,
        event_config: Optional[EventDetectionConfig] = None,
        metrics_collector=None,
    ):
        """
        Initialize Listener thread.

        Args:
            connection_manager: ConnectionManager instance
            state_queue: Queue to push states to
            event_queue: Queue to push events to
            stop_event: Event to signal thread stop
            poll_interval_ms: Polling interval in milliseconds
            health_check_interval_ms: Health check interval in milliseconds
            event_config: Event detection configuration
            metrics_collector: Optional MetricsCollector for tracking
        """
        super().__init__(name="ListenerThread", daemon=True)

        self.connection = connection_manager
        self.state_queue = state_queue
        self.event_queue = event_queue
        self.stop_event = stop_event
        self.poll_interval = poll_interval_ms / 1000.0
        self.health_check_interval = health_check_interval_ms / 1000.0
        self.event_config = event_config or EventDetectionConfig()
        self.metrics = metrics_collector

        # State tracking for event detection
        self._previous_state: Optional[Dict[str, Any]] = None
        self._known_colonist_ids: Set[int] = set()
        self._last_health_check = 0.0
        self._poll_count = 0
        self._event_count = 0

        # TASK-016: Connection state monitoring
        self._was_connected = False
        self._consecutive_failures = 0
        self._max_consecutive_failures = (
            5  # Trigger connection_lost event after this many failures
        )
        self._connection_lost_time: Optional[float] = None

        logger.info(
            f"Listener initialized: poll={poll_interval_ms}ms, "
            f"health_check={health_check_interval_ms}ms"
        )

    def run(self):
        """Main polling loop (runs in background thread)."""
        logger.info("Listener thread started")

        while not self.stop_event.is_set():
            loop_start = time.time()

            try:
                # Poll for state
                state = self._poll_state()

                if state:
                    # TASK-016: Connection recovery detection
                    if not self._was_connected or self._consecutive_failures > 0:
                        self._on_connection_restored()

                    self._was_connected = True
                    self._consecutive_failures = 0

                    # Push to state queue
                    self.state_queue.put(state)
                    self._poll_count += 1

                    if self.metrics:
                        self.metrics.record_state_received()

                    # Detect and enqueue events
                    events = self._detect_events(state)
                    for event_priority, event_data in events:
                        self.event_queue.put(event_data, event_priority)
                        self._event_count += 1

                        if self.metrics:
                            self.metrics.record_event_detected()

                    # Update previous state
                    self._previous_state = state
                else:
                    # TASK-016: Track consecutive failures for connection monitoring
                    self._consecutive_failures += 1
                    if self._consecutive_failures >= self._max_consecutive_failures:
                        self._on_connection_lost()

                # Health check
                if time.time() - self._last_health_check > self.health_check_interval:
                    self._perform_health_check()
                    self._last_health_check = time.time()

            except Exception as e:
                logger.error(f"Error in listener loop: {e}", exc_info=True)
                if self.metrics:
                    self.metrics.record_connection_error()
                time.sleep(self.poll_interval)
                continue

            # Maintain polling interval
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.poll_interval - elapsed)

            if sleep_time > 0:
                self.stop_event.wait(timeout=sleep_time)

        logger.info(
            f"Listener thread stopped (polls={self._poll_count}, "
            f"events={self._event_count})"
        )

    def _poll_state(self) -> Optional[Dict[str, Any]]:
        """
        Poll server for current state.

        Returns:
            Parsed state dictionary or None on error
        """
        try:
            # Create QUERY_STATE command
            command = CommandMessage()
            command.type = CommandType.QUERY_STATE

            # Send and receive response
            response = self.connection.send_command(command, timeout=1.0)

            if not response:
                return None

            # Parse response
            state = self._parse_state_message(response)
            return state

        except Exception as e:
            logger.debug(f"Poll state error: {e}")
            return None

    def _parse_state_message(self, message: StateMessage) -> Dict[str, Any]:
        """
        Parse protobuf StateMessage into dictionary.

        Args:
            message: StateMessage from server

        Returns:
            Parsed state dictionary
        """
        state = {
            "frame_id": message.frame_id,
            "timestamp": time.time(),  # Add current timestamp
            "colonists": [],
            "game_state": {
                "paused": getattr(message, "paused", False),
                "speed": getattr(message, "speed", 1),
            },
        }

        # Parse colonists if this is a RichStateMessage
        if hasattr(message, "colonists"):
            for colonist_msg in message.colonists:
                colonist = {
                    "id": colonist_msg.thing_id,
                    "name": colonist_msg.name,
                    "position": {
                        "x": colonist_msg.position.x,
                        "y": colonist_msg.position.y,
                        "z": colonist_msg.position.z,
                    },
                    "health": colonist_msg.health_percentage,
                    "current_job": colonist_msg.current_job.job_def
                    if colonist_msg.HasField("current_job")
                    else None,
                }

                # Add velocity if present
                if colonist_msg.HasField("velocity"):
                    colonist["velocity"] = {
                        "x": colonist_msg.velocity.x,
                        "y": colonist_msg.velocity.y,
                        "z": colonist_msg.velocity.z,
                    }

                state["colonists"].append(colonist)

        return state

    def _detect_events(self, current_state: Dict[str, Any]) -> list:
        """
        Detect events by comparing current state to previous state.

        Args:
            current_state: Current game state

        Returns:
            List of (priority, event_data) tuples
        """
        if not self._previous_state:
            # First state - initialize tracking
            self._initialize_tracking(current_state)
            return []

        events = []

        # Detect colonist events
        colonist_events = self._detect_colonist_events(
            current_state.get("colonists", []),
            self._previous_state.get("colonists", []),
        )
        events.extend(colonist_events)

        return events

    def _initialize_tracking(self, state: Dict[str, Any]):
        """Initialize tracking from first state."""
        colonists = state.get("colonists", [])
        self._known_colonist_ids = {c["id"] for c in colonists}
        logger.info(f"Initialized tracking: {len(self._known_colonist_ids)} colonists")

    def _detect_colonist_events(
        self, current_colonists: list, previous_colonists: list
    ) -> list:
        """
        Detect colonist-related events.

        Args:
            current_colonists: Current colonist list
            previous_colonists: Previous colonist list

        Returns:
            List of (priority, event_data) tuples
        """
        events = []

        # Build lookup maps
        current_map = {c["id"]: c for c in current_colonists}
        previous_map = {c["id"]: c for c in previous_colonists}

        current_ids = set(current_map.keys())
        previous_ids = set(previous_map.keys())

        # Detect new colonists
        if self.event_config.detect_new_colonists:
            new_ids = current_ids - previous_ids
            for colonist_id in new_ids:
                colonist = current_map[colonist_id]
                events.append(
                    (
                        EventPriority.MEDIUM,
                        {
                            "type": "colonist_joined",
                            "colonist_id": colonist_id,
                            "name": colonist["name"],
                            "timestamp": time.time(),
                        },
                    )
                )
                self._known_colonist_ids.add(colonist_id)

        # Detect dead/missing colonists
        if self.event_config.detect_dead_colonists:
            missing_ids = previous_ids - current_ids
            for colonist_id in missing_ids:
                colonist = previous_map[colonist_id]
                events.append(
                    (
                        EventPriority.HIGH,
                        {
                            "type": "colonist_missing",
                            "colonist_id": colonist_id,
                            "name": colonist["name"],
                            "last_health": colonist.get("health", 0),
                            "timestamp": time.time(),
                        },
                    )
                )
                self._known_colonist_ids.discard(colonist_id)

        # Check existing colonists for events
        for colonist_id in current_ids & previous_ids:
            current = current_map[colonist_id]
            previous = previous_map[colonist_id]

            # Health change events
            current_health = current.get("health", 1.0)
            previous_health = previous.get("health", 1.0)

            # Critical health
            if (
                current_health < self.event_config.health_critical_threshold
                and previous_health >= self.event_config.health_critical_threshold
            ):
                events.append(
                    (
                        EventPriority.CRITICAL,
                        {
                            "type": "health_critical",
                            "colonist_id": colonist_id,
                            "name": current["name"],
                            "health": current_health,
                            "timestamp": time.time(),
                        },
                    )
                )

            # Warning health
            elif (
                current_health < self.event_config.health_warning_threshold
                and previous_health >= self.event_config.health_warning_threshold
            ):
                events.append(
                    (
                        EventPriority.HIGH,
                        {
                            "type": "health_warning",
                            "colonist_id": colonist_id,
                            "name": current["name"],
                            "health": current_health,
                            "timestamp": time.time(),
                        },
                    )
                )

            # Job change events
            if self.event_config.detect_job_changes:
                current_job = current.get("current_job")
                previous_job = previous.get("current_job")

                if current_job != previous_job and current_job:
                    events.append(
                        (
                            EventPriority.LOW,
                            {
                                "type": "job_changed",
                                "colonist_id": colonist_id,
                                "name": current["name"],
                                "old_job": previous_job,
                                "new_job": current_job,
                                "timestamp": time.time(),
                            },
                        )
                    )

        return events

    def _perform_health_check(self):
        """Perform connection health check."""
        if not self.connection.is_healthy():
            logger.warning("Connection unhealthy, attempting reconnection")
            if self.connection.reconnect():
                logger.info("Reconnection successful")
                if self.metrics:
                    self.metrics.record_reconnection()
            else:
                logger.error("Reconnection failed")

    def _on_connection_lost(self):
        """
        TASK-016/018: Handle connection loss detection.
        Emits connection_lost event to EventQueue.
        """
        if self._connection_lost_time is not None:
            return  # Already in disconnected state

        self._connection_lost_time = time.time()
        self._was_connected = False

        logger.warning(
            f"Connection lost after {self._consecutive_failures} consecutive failures"
        )

        # TASK-018: Emit connection_lost event
        event_data = {
            "type": "connection_lost",
            "timestamp": self._connection_lost_time,
            "consecutive_failures": self._consecutive_failures,
        }
        self.event_queue.put(event_data, EventPriority.CRITICAL)

        if self.metrics:
            self.metrics.record_connection_error()

    def _on_connection_restored(self):
        """
        TASK-016/018: Handle connection restoration.
        Emits connection_restored event to EventQueue.
        """
        downtime = 0.0
        if self._connection_lost_time is not None:
            downtime = time.time() - self._connection_lost_time

        self._connection_lost_time = None

        if downtime > 0:
            logger.info(f"Connection restored after {downtime:.1f}s downtime")

            # TASK-018: Emit connection_restored event
            event_data = {
                "type": "connection_restored",
                "timestamp": time.time(),
                "downtime_seconds": downtime,
            }
            self.event_queue.put(event_data, EventPriority.HIGH)

            if self.metrics:
                self.metrics.record_reconnection()

    def get_stats(self) -> Dict[str, Any]:
        """Get listener statistics."""
        return {
            "poll_count": self._poll_count,
            "event_count": self._event_count,
            "known_colonists": len(self._known_colonist_ids),
            "was_connected": self._was_connected,
            "consecutive_failures": self._consecutive_failures,
            "connection_lost_time": self._connection_lost_time,
        }
