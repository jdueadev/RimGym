"""
Policy Interface

Abstract base class for all agent policies (Executive and Reflex).
Defines the contract for policy implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Policy(ABC):
    """
    Abstract base class for agent policies.

    All policies must implement the decide() method which takes game state
    and returns a list of actions to execute.

    Policies can be either:
    - Executive: High-level strategic decisions (10-100ms latency budget)
    - Reflex: Tactical immediate responses (<10ms latency budget)
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize policy.

        Args:
            name: Human-readable policy name for logging
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._decision_count = 0
        self._error_count = 0

    @abstractmethod
    def decide(self, state: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Make decisions based on current game state.

        Args:
            state: Current game state dictionary with keys:
                - frame_id: Current game frame number
                - timestamp: State capture timestamp
                - colonists: List of colonist data
                - global_state: Global game information

        Returns:
            List of action dictionaries, or None if no actions needed.
            Each action dict should have:
                - type: Action type string (e.g., "MOVE", "ATTACK")
                - target: Target identifier
                - parameters: Action-specific parameters

        Raises:
            PolicyError: If policy encounters unrecoverable error
        """
        pass

    def reset(self):
        """
        Reset policy state (called on episode reset).

        Subclasses can override to reset internal state.
        """
        self._decision_count = 0
        self._error_count = 0

    def get_stats(self) -> Dict[str, int]:
        """
        Get policy execution statistics.

        Returns:
            Dictionary with decision_count and error_count
        """
        return {
            "name": self.name,
            "decision_count": self._decision_count,
            "error_count": self._error_count,
        }

    def _record_decision(self):
        """Internal: Record successful decision."""
        self._decision_count += 1

    def _record_error(self):
        """Internal: Record error."""
        self._error_count += 1


class PolicyError(Exception):
    """Exception raised when policy encounters unrecoverable error."""

    pass
