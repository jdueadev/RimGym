"""
Reflex Policy

Fast heuristic-based tactical responses for urgent events.
Designed for <10ms latency budget.
"""

import logging
from typing import Any, Dict, List, Optional

from .policy import Policy

logger = logging.getLogger(__name__)


class ReflexPolicy(Policy):
    """
    Reflex policy for fast tactical responses.

    Implements heuristic-based reactions to urgent events:
    - Critical health → Immediate medical attention
    - Colonist missing → Alert/search
    - Job changed → Monitor for safety

    Designed for <10ms decision time with simple rule evaluation.

    Configuration:
        health_critical_threshold: Health % for emergency response (default: 0.2)
        enable_auto_rescue: Auto-generate rescue actions (default: True)
        enable_auto_draft: Auto-draft for combat (default: False)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reflex policy.

        Args:
            config: Optional configuration dict
        """
        cfg = config or {}
        super().__init__(name="ReflexPolicy", config=cfg)

        # Default configuration
        self.health_critical = cfg.get("health_critical_threshold", 0.2)
        self.enable_auto_rescue = cfg.get("enable_auto_rescue", True)
        self.enable_auto_draft = cfg.get("enable_auto_draft", False)

        logger.info(
            "ReflexPolicy initialized: health_critical=%.2f, auto_rescue=%s",
            self.health_critical,
            self.enable_auto_rescue,
        )

    def decide(self, state: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Generate tactical response to urgent event.

        For ReflexPolicy, the "state" parameter is actually an event dict.
        Fast heuristic evaluation (<10ms target).

        Args:
            state: Event dictionary from EventQueue (following Policy interface)

        Returns:
            List of action dictionaries, or None if no action needed
        """
        try:
            self._record_decision()

            # Treat state as event for reflex layer
            event = state
            event_type = event.get("type")
            priority = event.get("priority")

            logger.debug(
                "ReflexPolicy processing event: %s (priority: %s)",
                event_type,
                priority,
            )

            # Route to appropriate handler
            if event_type == "health_critical":
                return self._handle_health_critical(event)
            elif event_type == "colonist_missing":
                return self._handle_colonist_missing(event)
            elif event_type == "health_warning":
                return self._handle_health_warning(event)
            elif event_type == "colonist_joined":
                return self._handle_colonist_joined(event)
            elif event_type == "job_changed":
                return self._handle_job_changed(event)
            else:
                logger.debug("No reflex action for event type: %s", event_type)
                return None

        except Exception as e:
            self._record_error()
            logger.error("ReflexPolicy error: %s", e, exc_info=True)
            return None

    def _handle_health_critical(
        self, event: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Handle critical health event.

        Immediate rescue if enabled.

        Args:
            event: Health critical event

        Returns:
            List of rescue actions or None
        """
        if not self.enable_auto_rescue:
            return None

        colonist_id = event.get("colonist_id")
        health = event.get("health", 0.0)

        if health >= self.health_critical:
            # False alarm, not critical enough
            return None

        # Generate immediate rescue action
        action = {
            "type": "RESCUE_COLONIST",
            "colonist_id": colonist_id,
            "priority": "critical",
            "reason": f"Critical health: {health * 100:.1f}%",
            "source": "reflex",
        }

        logger.info(
            "ReflexPolicy: Emergency rescue for colonist %s (health: %.1f%%)",
            colonist_id,
            health * 100,
        )

        return [action]

    def _handle_colonist_missing(
        self, event: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Handle colonist missing event.

        Alert or search action.

        Args:
            event: Colonist missing event

        Returns:
            List of alert actions or None
        """
        colonist_id = event.get("colonist_id")
        colonist_name = event.get("colonist_name", "Unknown")

        # Generate alert action
        action = {
            "type": "ALERT",
            "message": f"Colonist {colonist_name} (ID: {colonist_id}) is missing!",
            "priority": "high",
            "source": "reflex",
        }

        logger.warning(
            "ReflexPolicy: Colonist missing alert for %s (ID: %s)",
            colonist_name,
            colonist_id,
        )

        return [action]

    def _handle_health_warning(
        self, event: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Handle health warning event.

        For reflex layer, we typically don't act on warnings
        (Executive layer handles those).

        Args:
            event: Health warning event

        Returns:
            None (let Executive handle)
        """
        # Reflex layer focuses on CRITICAL events
        # Let Executive handle warnings strategically
        return None

    def _handle_colonist_joined(
        self, event: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Handle new colonist event.

        No immediate tactical response needed.

        Args:
            event: Colonist joined event

        Returns:
            None
        """
        # No tactical reflex needed for new colonists
        # Executive layer can handle strategic assignments
        return None

    def _handle_job_changed(
        self, event: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Handle job changed event.

        Monitor for safety-critical job transitions.

        Args:
            event: Job changed event

        Returns:
            Actions if safety concern, None otherwise
        """
        new_job = event.get("new_job", "None")

        # Check for concerning job changes
        dangerous_jobs = ["AttackMelee", "AttackStatic", "Hunt"]

        if new_job in dangerous_jobs:
            colonist_id = event.get("colonist_id")

            # Check if colonist health is too low for combat
            health = event.get("health", 1.0)
            if health < 0.5:  # <50% health entering combat
                action = {
                    "type": "INTERRUPT_JOB",
                    "colonist_id": colonist_id,
                    "reason": f"Low health ({health * 100:.1f}%) for dangerous job: {new_job}",
                    "priority": "high",
                    "source": "reflex",
                }

                logger.warning(
                    "ReflexPolicy: Interrupting dangerous job %s for low-health colonist %s",
                    new_job,
                    colonist_id,
                )

                return [action]

        return None

    def reset(self):
        """
        Reset policy state for new episode.

        Reflex policy is stateless, so just reset counters.
        """
        super().reset()
        logger.info("ReflexPolicy reset")
