"""
Actor Thread

Tactical reflex response thread that consumes urgent events and generates immediate actions.
Implements the Reflex layer of the hierarchical policy system.
"""

import logging
import queue
import threading
import time

from policies.policy import Policy

from .queues import ActionQueue, EventQueue

logger = logging.getLogger(__name__)

# Target latency budget for reflex reactions in milliseconds
REFLEX_LATENCY_BUDGET_MS = 10.0


class ActorThread(threading.Thread):
    """
    Actor thread for tactical reflex responses.

    Consumes high-priority events from EventQueue, runs Reflex policy,
    and generates immediate tactical actions for the ActionQueue.

    Designed for <10ms latency budget per reaction.

    Key features:
    - Priority-based event processing (CRITICAL and HIGH first)
    - Ultra-low latency reactions (<10ms target)
    - Can override Executive policy decisions for same colonist
    - Safety-critical actions take precedence

    Attributes:
        policy: Policy instance to use for reflex decisions
        event_queue: Queue to consume events from
        action_queue: Queue to produce actions to
        stop_event: Event to signal thread shutdown
        timeout_ms: Queue get timeout in milliseconds
        metrics_collector: Optional metrics collector
    """

    def __init__(
        self,
        policy: Policy,
        event_queue: EventQueue,
        action_queue: ActionQueue,
        stop_event: threading.Event,
        timeout_ms: int = 10,
        metrics_collector=None,
    ):
        """
        Initialize actor thread.

        Args:
            policy: Reflex policy instance
            event_queue: Event queue to consume from
            action_queue: Action queue to produce to
            stop_event: Threading event for shutdown
            timeout_ms: Timeout for queue operations
            metrics_collector: Optional metrics collector
        """
        super().__init__(name="ActorThread", daemon=True)

        self.policy = policy
        self.event_queue = event_queue
        self.action_queue = action_queue
        self.stop_event = stop_event
        self.timeout_ms = timeout_ms
        self.metrics_collector = metrics_collector

        # Statistics
        self.events_processed = 0
        self.actions_generated = 0
        self.policy_errors = 0
        self.latency_warnings = 0

        logger.info("ActorThread initialized with policy: %s", type(policy).__name__)

    def run(self):
        """
        Main actor loop.

        Continuously consumes events from EventQueue (prioritized),
        invokes reflex policy, and generates tactical actions.

        Monitors latency and warns if reactions exceed <10ms budget.
        """
        logger.info("ActorThread started")

        try:
            while not self.stop_event.is_set():
                try:
                    # Get event with timeout (priority-based)
                    timeout_sec = self.timeout_ms / 1000.0
                    event = self.event_queue.get(timeout=timeout_sec)

                    # If we got a valid event, process it
                    if event is None:
                        continue

                    start_time = time.time()

                    # Log event processing
                    event_type = event.get("type", "unknown")
                    priority = event.get("priority", "unknown")
                    logger.debug(
                        "Processing %s event: %s (priority: %s)",
                        priority,
                        event_type,
                        priority,
                    )

                    # Invoke reflex policy
                    try:
                        actions = self.policy.decide(event)

                        if actions:
                            # Generate actions with priority override
                            for action in actions:
                                # Mark as reflex action for conflict resolution
                                action["source"] = "reflex"
                                action["priority"] = "high"

                                # Put action in queue (may fail if full)
                                success = self.action_queue.put(action)
                                if success:
                                    self.actions_generated += 1
                                    logger.debug(
                                        "Generated reflex action: %s",
                                        action.get("type"),
                                    )
                                else:
                                    logger.warning(
                                        "ActionQueue full, dropping reflex action: %s",
                                        action.get("type"),
                                    )

                    except Exception as e:
                        self.policy_errors += 1
                        logger.error(
                            "Reflex policy error for event %s: %s",
                            event_type,
                            e,
                            exc_info=True,
                        )

                    # Check latency
                    latency_ms = (time.time() - start_time) * 1000
                    if latency_ms > REFLEX_LATENCY_BUDGET_MS:
                        self.latency_warnings += 1
                        logger.warning(
                            "Reflex reaction took %.2fms (>%.0fms budget) for event: %s",
                            latency_ms,
                            REFLEX_LATENCY_BUDGET_MS,
                            event_type,
                        )

                    self.events_processed += 1

                    # Update metrics
                    if self.metrics_collector:
                        self.metrics_collector.record_event(
                            "actor_reaction", latency_ms
                        )

                except queue.Empty:
                    # Normal timeout, continue
                    continue

        except Exception as e:
            logger.error("ActorThread crashed: %s", e, exc_info=True)
        finally:
            logger.info(
                "ActorThread stopping. Processed: %d events, Generated: %d actions, Errors: %d",
                self.events_processed,
                self.actions_generated,
                self.policy_errors,
            )

    def get_statistics(self) -> dict:
        """
        Get actor thread statistics.

        Returns:
            Dict with events_processed, actions_generated, policy_errors, latency_warnings
        """
        return {
            "events_processed": self.events_processed,
            "actions_generated": self.actions_generated,
            "policy_errors": self.policy_errors,
            "latency_warnings": self.latency_warnings,
            "policy_stats": self.policy.get_stats(),
        }
