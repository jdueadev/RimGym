"""Metrics collection and monitoring for the RimGym client.

Tracks performance, throughput, latencies, and queue health.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""

    # Throughput
    states_per_second: float = 0.0
    actions_per_second: float = 0.0
    events_per_second: float = 0.0

    # Latencies (ms)
    observation_latency_ms: float = 0.0
    inference_latency_ms: float = 0.0
    action_latency_ms: float = 0.0

    # Queue health
    state_queue_size: int = 0
    event_queue_size: int = 0
    action_queue_size: int = 0
    state_queue_dropped: int = 0
    event_queue_dropped: int = 0
    action_queue_dropped: int = 0

    # Connection
    connection_healthy: bool = False
    reconnections: int = 0
    connection_errors: int = 0

    # Timestamps
    timestamp: float = field(default_factory=time.time)
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "throughput": {
                "states_per_second": self.states_per_second,
                "actions_per_second": self.actions_per_second,
                "events_per_second": self.events_per_second,
            },
            "latency_ms": {
                "observation": self.observation_latency_ms,
                "inference": self.inference_latency_ms,
                "action": self.action_latency_ms,
            },
            "queues": {
                "state": {
                    "size": self.state_queue_size,
                    "dropped": self.state_queue_dropped,
                },
                "event": {
                    "size": self.event_queue_size,
                    "dropped": self.event_queue_dropped,
                },
                "action": {
                    "size": self.action_queue_size,
                    "dropped": self.action_queue_dropped,
                },
            },
            "connection": {
                "healthy": self.connection_healthy,
                "reconnections": self.reconnections,
                "errors": self.connection_errors,
            },
            "uptime_seconds": self.uptime_seconds,
        }


class MetricsCollector:
    """
    Collects and aggregates metrics from client components.

    Thread-safe metrics collection with sliding window statistics.
    """

    def __init__(self, window_size_seconds: float = 10.0):
        """
        Initialize metrics collector.

        Args:
            window_size_seconds: Size of sliding window for rate calculations
        """
        self.window_size = window_size_seconds
        self._start_time = time.time()

        # Counters
        self._counters: Dict[str, int] = {
            "states_received": 0,
            "actions_sent": 0,
            "events_detected": 0,
            "reconnections": 0,
            "connection_errors": 0,
        }

        # Latency tracking (sliding window)
        self._latencies: Dict[str, deque] = {
            "observation": deque(maxlen=100),
            "inference": deque(maxlen=100),
            "action": deque(maxlen=100),
        }

        # Rate tracking (timestamped events)
        self._events: Dict[str, deque] = {
            "states": deque(maxlen=1000),
            "actions": deque(maxlen=1000),
            "events": deque(maxlen=1000),
        }

        # Queue references (set by client)
        self._state_queue = None
        self._event_queue = None
        self._action_queue = None

        # Connection reference
        self._connection = None

        # Thread safety
        self._lock = threading.Lock()

    def set_queues(self, state_queue, event_queue, action_queue):
        """Set queue references for monitoring."""
        self._state_queue = state_queue
        self._event_queue = event_queue
        self._action_queue = action_queue

    def set_connection(self, connection):
        """Set connection reference for monitoring."""
        self._connection = connection

    def record_state_received(self):
        """Record that a state was received."""
        with self._lock:
            self._counters["states_received"] += 1
            self._events["states"].append(time.time())

    def record_action_sent(self):
        """Record that an action was sent."""
        with self._lock:
            self._counters["actions_sent"] += 1
            self._events["actions"].append(time.time())

    def record_event_detected(self):
        """Record that an event was detected."""
        with self._lock:
            self._counters["events_detected"] += 1
            self._events["events"].append(time.time())

    def record_reconnection(self):
        """Record a reconnection attempt."""
        with self._lock:
            self._counters["reconnections"] += 1

    def record_connection_error(self):
        """Record a connection error."""
        with self._lock:
            self._counters["connection_errors"] += 1

    def record_latency(self, category: str, latency_ms: float):
        """
        Record a latency measurement.

        Args:
            category: 'observation', 'inference', or 'action'
            latency_ms: Latency in milliseconds
        """
        with self._lock:
            if category in self._latencies:
                self._latencies[category].append(latency_ms)

    def get_metrics(self) -> PerformanceMetrics:
        """
        Get current metrics snapshot.

        Returns:
            PerformanceMetrics object with current statistics
        """
        with self._lock:
            now = time.time()
            cutoff = now - self.window_size

            # Calculate rates (events per second in window)
            states_in_window = sum(1 for t in self._events["states"] if t >= cutoff)
            actions_in_window = sum(1 for t in self._events["actions"] if t >= cutoff)
            events_in_window = sum(1 for t in self._events["events"] if t >= cutoff)

            states_per_second = states_in_window / self.window_size
            actions_per_second = actions_in_window / self.window_size
            events_per_second = events_in_window / self.window_size

            # Calculate average latencies
            obs_latency = self._avg_latency("observation")
            inf_latency = self._avg_latency("inference")
            act_latency = self._avg_latency("action")

            # Get queue stats
            state_size = self._state_queue.qsize() if self._state_queue else 0
            event_size = self._event_queue.qsize() if self._event_queue else 0
            action_size = self._action_queue.qsize() if self._action_queue else 0

            state_dropped = self._state_queue.dropped_count if self._state_queue else 0
            event_dropped = self._event_queue.dropped_count if self._event_queue else 0
            action_dropped = (
                self._action_queue.dropped_count if self._action_queue else 0
            )

            # Connection health
            connection_healthy = (
                self._connection.is_connected() if self._connection else False
            )

            return PerformanceMetrics(
                states_per_second=states_per_second,
                actions_per_second=actions_per_second,
                events_per_second=events_per_second,
                observation_latency_ms=obs_latency,
                inference_latency_ms=inf_latency,
                action_latency_ms=act_latency,
                state_queue_size=state_size,
                event_queue_size=event_size,
                action_queue_size=action_size,
                state_queue_dropped=state_dropped,
                event_queue_dropped=event_dropped,
                action_queue_dropped=action_dropped,
                connection_healthy=connection_healthy,
                reconnections=self._counters["reconnections"],
                connection_errors=self._counters["connection_errors"],
                uptime_seconds=now - self._start_time,
            )

    def _avg_latency(self, category: str) -> float:
        """Calculate average latency for a category."""
        latencies = self._latencies.get(category, [])
        if not latencies:
            return 0.0
        return sum(latencies) / len(latencies)

    def get_counters(self) -> Dict[str, int]:
        """Get raw counter values."""
        with self._lock:
            return self._counters.copy()

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._counters = {k: 0 for k in self._counters}
            for deq in self._latencies.values():
                deq.clear()
            for deq in self._events.values():
                deq.clear()
            self._start_time = time.time()
