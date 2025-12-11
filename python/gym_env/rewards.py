"""
Reward Function for RimWorld Gymnasium Environment

Calculates rewards based on colonist survival, health, mood, and productivity.
"""

from typing import Any, Dict, Optional

import numpy as np


class RewardCalculator:
    """
    Reward calculator for RimWorld environment.

    Computes rewards based on multiple factors:
    - Colonist survival (highest priority)
    - Health maintenance
    - Mood/happiness
    - Productivity (work completion)
    - Resource management

    Rewards are normalized to roughly [-1, 1] per step.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reward calculator.

        Args:
            config: Optional configuration dict for reward weights
        """
        cfg = config or {}

        # Reward weights
        self.weight_survival = cfg.get("weight_survival", 10.0)
        self.weight_health = cfg.get("weight_health", 2.0)
        self.weight_mood = cfg.get("weight_mood", 1.0)
        self.weight_productivity = cfg.get("weight_productivity", 0.5)
        self.weight_resources = cfg.get("weight_resources", 0.3)

        # Penalties
        self.penalty_death = cfg.get("penalty_death", -20.0)
        self.penalty_critical_health = cfg.get("penalty_critical_health", -5.0)
        self.penalty_mental_break = cfg.get("penalty_mental_break", -3.0)

        # Previous state for delta computation
        self._previous_state: Optional[Dict[str, Any]] = None

    def compute_reward(
        self,
        state: Dict[str, Any],
        action: Optional[np.ndarray] = None,
        done: bool = False,
    ) -> float:
        """
        Compute reward for current state and action.

        Args:
            state: Current game state
            action: Action taken (optional, for action-based rewards)
            done: Whether episode is terminal

        Returns:
            Reward value (typically in [-1, 1] per step)
        """
        if self._previous_state is None:
            # First step, no reward yet
            self._previous_state = state
            return 0.0

        reward = 0.0

        # Survival reward (most important)
        reward += self._compute_survival_reward(state, self._previous_state)

        # Health reward
        reward += self._compute_health_reward(state)

        # Mood reward
        reward += self._compute_mood_reward(state)

        # Productivity reward (future)
        # reward += self._compute_productivity_reward(state, self._previous_state)

        # Resource management reward (future)
        # reward += self._compute_resource_reward(state, self._previous_state)

        # Terminal state bonus/penalty
        if done:
            reward += self._compute_terminal_reward(state)

        # Update previous state
        self._previous_state = state

        # Clip to reasonable range
        return np.clip(reward, -10.0, 10.0)

    def _compute_survival_reward(
        self, state: Dict[str, Any], prev_state: Dict[str, Any]
    ) -> float:
        """
        Compute reward based on colonist survival.

        Args:
            state: Current state
            prev_state: Previous state

        Returns:
            Survival reward (negative if colonists died)
        """
        curr_colonists = state.get("colonists", [])
        prev_colonists = prev_state.get("colonists", [])

        curr_count = len(curr_colonists)
        prev_count = len(prev_colonists)

        # Death penalty
        if curr_count < prev_count:
            deaths = prev_count - curr_count
            return self.penalty_death * deaths

        # Survival bonus (small constant reward for keeping colonists alive)
        return self.weight_survival * curr_count * 0.01

    def _compute_health_reward(self, state: Dict[str, Any]) -> float:
        """
        Compute reward based on colonist health.

        Args:
            state: Current state

        Returns:
            Health reward (negative if critical health)
        """
        colonists = state.get("colonists", [])

        if not colonists:
            return 0.0

        total_health = 0.0
        critical_count = 0

        for colonist in colonists:
            health = colonist.get("health", 1.0)
            total_health += health

            if health < 0.2:  # Critical health
                critical_count += 1

        # Average health reward
        avg_health = total_health / len(colonists)
        health_reward = self.weight_health * (avg_health - 0.5)  # Centered at 0.5

        # Critical health penalty
        if critical_count > 0:
            health_reward += self.penalty_critical_health * critical_count

        return health_reward

    def _compute_mood_reward(self, state: Dict[str, Any]) -> float:
        """
        Compute reward based on colonist mood.

        Args:
            state: Current state

        Returns:
            Mood reward
        """
        colonists = state.get("colonists", [])

        if not colonists:
            return 0.0

        total_mood = 0.0
        mental_break_count = 0

        for colonist in colonists:
            mood = colonist.get("mood", 0.5)
            total_mood += mood

            # Check for mental break (very low mood)
            if mood < 0.2:
                mental_break_count += 1

        # Average mood reward
        avg_mood = total_mood / len(colonists)
        mood_reward = self.weight_mood * (avg_mood - 0.5)  # Centered at 0.5

        # Mental break penalty
        if mental_break_count > 0:
            mood_reward += self.penalty_mental_break * mental_break_count

        return mood_reward

    def _compute_productivity_reward(
        self, state: Dict[str, Any], prev_state: Dict[str, Any]
    ) -> float:
        """
        Compute reward based on productivity (work completion).

        Future implementation: track work completion, building progress, etc.

        Args:
            state: Current state
            prev_state: Previous state

        Returns:
            Productivity reward
        """
        # TODO: Implement when work tracking available
        return 0.0

    def _compute_resource_reward(
        self, state: Dict[str, Any], prev_state: Dict[str, Any]
    ) -> float:
        """
        Compute reward based on resource management.

        Future implementation: track food, medicine, materials.

        Args:
            state: Current state
            prev_state: Previous state

        Returns:
            Resource management reward
        """
        # TODO: Implement when resource tracking available
        return 0.0

    def _compute_terminal_reward(self, state: Dict[str, Any]) -> float:
        """
        Compute bonus/penalty for terminal state.

        Args:
            state: Final state

        Returns:
            Terminal reward
        """
        colonists = state.get("colonists", [])

        # Large penalty if all colonists died
        if len(colonists) == 0:
            return -50.0

        # Small bonus for surviving to natural episode end
        return 5.0

    def reset(self):
        """Reset calculator for new episode."""
        self._previous_state = None
