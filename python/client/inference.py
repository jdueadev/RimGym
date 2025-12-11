"""
Inference Thread

Strategic policy execution thread that consumes states and generates actions.
Implements the Executive layer of the hierarchical policy system.
"""

import logging
import queue
import threading
import time

from policies.policy import Policy

from .queues import ActionQueue, StateQueue

logger = logging.getLogger(__name__)


class InferenceThread(threading.Thread):
    """
    Inference thread for strategic decision-making.

    Consumes states from StateQueue, runs Executive policy,
    and generates actions for the ActionQueue.

    Designed for 10-100ms latency budget per decision.

    Attributes:
        policy: Policy instance to use for decisions
        state_queue: Queue to consume states from
        action_queue: Queue to produce actions to
        stop_event: Event to signal thread shutdown
        timeout_ms: Queue get timeout in milliseconds
        metrics_collector: Optional metrics collector
    """

    def __init__(
        self,
        policy: Policy,
        state_queue: StateQueue,
        action_queue: ActionQueue,
        stop_event: threading.Event,
        timeout_ms: int = 100,
        metrics_collector=None,
    ):
        """
        Initialize inference thread.

        Args:
            policy: Policy instance for decision-making
            state_queue: Queue to consume states from
            action_queue: Queue to produce actions to
            stop_event: Event to signal shutdown
            timeout_ms: Queue timeout in milliseconds (default: 100ms)
            metrics_collector: Optional MetricsCollector instance
        """
        super().__init__(name="InferenceThread", daemon=True)

        self.policy = policy
        self.state_queue = state_queue
        self.action_queue = action_queue
        self.stop_event = stop_event
        self.timeout_ms = timeout_ms
        self.metrics_collector = metrics_collector

        # Statistics
        self._states_processed = 0
        self._actions_generated = 0
        self._policy_errors = 0
        self._total_latency_ms = 0.0

        logger.info(
            f"[InferenceThread] Initialized with policy={policy.name}, "
            f"timeout={timeout_ms}ms"
        )

    def run(self):
        """Main inference loop."""
        logger.info("[InferenceThread] Thread started")

        try:
            while not self.stop_event.is_set():
                self._inference_cycle()
        except Exception as e:
            logger.error(f"[InferenceThread] Fatal error: {e}", exc_info=True)
        finally:
            logger.info(
                f"[InferenceThread] Thread stopped. "
                f"Processed {self._states_processed} states, "
                f"generated {self._actions_generated} actions"
            )

    def _inference_cycle(self):
        """
        Single inference cycle: get state, run policy, queue actions.
        """
        try:
            # Get state from queue (blocking with timeout)
            timeout_sec = self.timeout_ms / 1000.0
            state = self.state_queue.get(timeout=timeout_sec)

            if state is None:
                return

            # Record state received
            self._states_processed += 1

            if self.metrics_collector:
                self.metrics_collector.record_event("inference_state_received")

            # Run policy (with timing)
            start_time = time.perf_counter()

            try:
                actions = self.policy.decide(state)
            except Exception as e:
                logger.error(f"[InferenceThread] Policy error: {e}", exc_info=True)
                self._policy_errors += 1
                if self.metrics_collector:
                    self.metrics_collector.record_event("inference_policy_error")
                return

            # Record latency
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            self._total_latency_ms += latency_ms

            if self.metrics_collector:
                self.metrics_collector.record_latency("inference_latency", latency_ms)

            # Log if exceeds budget
            if latency_ms > 100:
                logger.warning(
                    f"[InferenceThread] Policy latency {latency_ms:.2f}ms "
                    f"exceeds 100ms budget"
                )

            # Queue actions
            if actions:
                self._queue_actions(actions)
                self._actions_generated += len(actions)

                logger.debug(
                    f"[InferenceThread] Generated {len(actions)} actions "
                    f"in {latency_ms:.2f}ms"
                )

        except queue.Empty:
            # Timeout - no state available
            pass
        except Exception as e:
            logger.error(
                f"[InferenceThread] Error in inference cycle: {e}", exc_info=True
            )

    def _queue_actions(self, actions: list):
        """
        Queue actions to action queue.

        Args:
            actions: List of action dictionaries
        """
        for action in actions:
            try:
                self.action_queue.put(action)

                if self.metrics_collector:
                    self.metrics_collector.record_event("inference_action_queued")

            except queue.Full:
                logger.warning("[InferenceThread] Action queue full, dropping action")
                if self.metrics_collector:
                    self.metrics_collector.record_event("inference_action_dropped")

    def get_stats(self) -> dict:
        """
        Get inference thread statistics.

        Returns:
            Dictionary with thread stats
        """
        avg_latency = (
            self._total_latency_ms / self._states_processed
            if self._states_processed > 0
            else 0
        )

        return {
            "states_processed": self._states_processed,
            "actions_generated": self._actions_generated,
            "policy_errors": self._policy_errors,
            "avg_latency_ms": avg_latency,
            "policy_stats": self.policy.get_stats(),
        }
