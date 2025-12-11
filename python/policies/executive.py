"""
Executive Policy

Rule-based strategic policy for high-level decision-making.
Implements simple colonist management heuristics.
"""

import logging
from typing import Any, Dict, List, Optional

from .policy import Policy

logger = logging.getLogger(__name__)


class ExecutivePolicy(Policy):
    """
    Executive policy implementing strategic decision-making.

    Uses simple rule-based heuristics for:
    - Health management (send injured colonists to medical beds)
    - Threat response (draft colonists when under attack)
    - Resource management (prioritize critical tasks)

    Designed for 10-100ms latency budget.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize executive policy.

        Config options:
            - health_critical_threshold: Health % to trigger medical (default: 0.3)
            - health_warning_threshold: Health % for monitoring (default: 0.5)
            - enable_auto_draft: Auto-draft during threats (default: True)
            - enable_health_management: Enable health checks (default: True)
        """
        super().__init__(name="ExecutivePolicy", config=config)

        cfg = config or {}
        self.health_critical = cfg.get("health_critical_threshold", 0.3)
        self.health_warning = cfg.get("health_warning_threshold", 0.5)
        self.auto_draft = cfg.get("enable_auto_draft", True)
        self.health_management = cfg.get("enable_health_management", True)

        logger.info(
            f"[ExecutivePolicy] Initialized with health_critical={self.health_critical}, "
            f"health_warning={self.health_warning}, auto_draft={self.auto_draft}"
        )

    def decide(self, state: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Make strategic decisions based on game state.

        Decision logic:
        1. Check colonist health → send injured to medical beds
        2. Check for threats → draft capable colonists
        3. Check resource needs → prioritize critical tasks

        Args:
            state: Game state with colonists, global_state, frame_id

        Returns:
            List of action dictionaries, or None if no actions
        """
        try:
            actions = []

            colonists = state.get("colonists", [])

            if not colonists:
                logger.debug("[ExecutivePolicy] No colonists in state")
                return None

            # Rule 1: Health Management
            if self.health_management:
                health_actions = self._check_health(colonists)
                if health_actions:
                    actions.extend(health_actions)

            # Rule 2: Threat Response (placeholder for future)
            # threats = state.get("threats", [])
            # if self.auto_draft and threats:
            #     draft_actions = self._respond_to_threats(colonists, threats)
            #     actions.extend(draft_actions)

            # Record successful decision
            self._record_decision()

            if actions:
                logger.info(f"[ExecutivePolicy] Generated {len(actions)} actions")
                return actions

            return None

        except Exception as e:
            logger.error(f"[ExecutivePolicy] Error in decide(): {e}", exc_info=True)
            self._record_error()
            return None

    def _check_health(self, colonists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check colonist health and generate medical actions.

        Args:
            colonists: List of colonist dictionaries

        Returns:
            List of medical actions (send to bed, prioritize doctor)
        """
        actions = []

        for colonist in colonists:
            colonist_id = colonist.get("id")
            health = colonist.get("health", 1.0)
            current_job = colonist.get("job", "")

            # Critical health - needs immediate medical attention
            if health < self.health_critical:
                logger.warning(
                    f"[ExecutivePolicy] Colonist {colonist_id} critical health: {health:.2%}"
                )

                # Only send to medical if not already there
                job_lower = current_job.lower() if current_job else ""
                if "medical" not in job_lower and "patient" not in job_lower:
                    actions.append(
                        {
                            "type": "SEND_TO_MEDICAL",
                            "target": colonist_id,
                            "priority": "CRITICAL",
                            "reason": f"Health critical: {health:.2%}",
                        }
                    )

            # Warning health - monitor
            elif health < self.health_warning:
                logger.info(
                    f"[ExecutivePolicy] Colonist {colonist_id} low health: {health:.2%}"
                )
                # Could add non-critical medical actions here

        return actions

    def reset(self):
        """Reset policy state."""
        super().reset()
        logger.info("[ExecutivePolicy] Policy reset")
