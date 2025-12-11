"""
RimWorld Gymnasium Environment

Standard RL environment interface compatible with Stable-Baselines3.
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from client import ClientConfig, SpectatorClient

from .rewards import RewardCalculator
from .spaces import ActionSpace, ObservationSpace

logger = logging.getLogger(__name__)


class RimWorldEnv(gym.Env):
    """
    Gymnasium environment for RimWorld.

    Provides standard RL interface with observation/action spaces,
    reward function, and episode management.

    Compatible with Stable-Baselines3 algorithms (PPO, A2C, DQN, etc.).
    """

    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        training_mode: bool = True,
        max_episode_steps: int = 10000,
        reward_config: Optional[Dict[str, Any]] = None,
        render_mode: Optional[str] = None,
    ):
        """
        Initialize RimWorld environment.

        Args:
            host: RimWorld server host
            port: RimWorld server port
            training_mode: Use training mode (deterministic stepping)
            max_episode_steps: Maximum steps per episode
            reward_config: Optional reward calculator configuration
            render_mode: Optional render mode ("human")
        """
        super().__init__()

        # Environment configuration
        self.host = host
        self.port = port
        self.training_mode = training_mode
        self.max_episode_steps = max_episode_steps
        self.render_mode = render_mode

        # Define spaces
        self.observation_space = ObservationSpace.create()
        self.action_space = ActionSpace.create()

        # Reward calculator
        self.reward_calculator = RewardCalculator(config=reward_config)

        # Client for RimWorld connection
        self.client: Optional[SpectatorClient] = None
        self._current_state: Optional[Dict[str, Any]] = None
        self._episode_step = 0
        self._episode_return = 0.0

        logger.info(
            f"RimWorldEnv initialized (mode={'training' if training_mode else 'inference'}, "
            f"max_steps={max_episode_steps})"
        )

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Reset environment for new episode.

        Args:
            seed: Random seed (for reproducibility)
            options: Optional reset options

        Returns:
            Tuple of (observation, info)
        """
        super().reset(seed=seed)

        logger.info("Resetting RimWorld environment...")

        # Close existing client if any
        if self.client is not None:
            self.client.stop()
            self.client = None

        # Create and start new client
        config = ClientConfig(
            host=self.host,
            port=self.port,
            training_mode=self.training_mode,
            inference_mode=not self.training_mode,
            executive_policy=None,  # RL agent controls actions
            reflex_policy=None,  # RL agent controls actions
        )

        self.client = SpectatorClient(config)
        self.client.start()

        # Wait for ready
        if not self.client.wait_ready(timeout=30.0):
            raise RuntimeError("Failed to connect to RimWorld server")

        # Send RESET command to server
        reset_successful = self._send_reset_command()
        if not reset_successful:
            raise RuntimeError("Failed to reset RimWorld game")

        # Get initial state
        self._current_state = self._get_state()

        # Reset episode tracking
        self._episode_step = 0
        self._episode_return = 0.0
        self.reward_calculator.reset()

        # Extract observation
        observation = ObservationSpace.extract_observation(self._current_state)

        info = {
            "episode_step": self._episode_step,
            "episode_return": self._episode_return,
            "colonist_count": len(self._current_state.get("colonists", [])),
        }

        logger.info("Environment reset complete")
        return observation, info

    def step(
        self, action: np.ndarray
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """
        Execute one environment step.

        Args:
            action: Action from RL agent [colonist_id, action_type, target_id]

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        if self.client is None or self._current_state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        # Decode action to RimWorld command
        action_dict = ActionSpace.decode_action(action, self._current_state)

        # Execute action (if valid)
        if action_dict is not None:
            self.client.action_queue.put(action_dict)

        # Step simulation forward
        if self.training_mode:
            # Training mode: advance N ticks deterministically
            self._send_step_command(ticks=60)  # 1 second
        else:
            # Inference mode: wait for state update
            time.sleep(0.1)  # 100ms

        # Get new state
        self._current_state = self._get_state()
        observation = ObservationSpace.extract_observation(self._current_state)

        # Compute reward
        reward = self.reward_calculator.compute_reward(
            self._current_state, action=action, done=False
        )

        # Check termination conditions
        colonists = self._current_state.get("colonists", [])
        terminated = len(colonists) == 0  # All colonists dead
        truncated = self._episode_step >= self.max_episode_steps  # Max steps reached

        # Update episode tracking
        self._episode_step += 1
        self._episode_return += reward

        info = {
            "episode_step": self._episode_step,
            "episode_return": self._episode_return,
            "colonist_count": len(colonists),
            "action_valid": action_dict is not None,
        }

        # Terminal reward
        if terminated or truncated:
            final_reward = self.reward_calculator.compute_reward(
                self._current_state, done=True
            )
            reward += final_reward
            info["episode_length"] = self._episode_step
            info["episode_return"] = self._episode_return
            logger.info(
                f"Episode ended: steps={self._episode_step}, return={self._episode_return:.2f}"
            )

        return observation, reward, terminated, truncated, info

    def close(self):
        """Clean up resources."""
        if self.client is not None:
            logger.info("Closing RimWorld environment...")
            self.client.stop()
            self.client = None

    def render(self):
        """Render environment (RimWorld game window handles rendering)."""
        if self.render_mode == "human":
            # RimWorld game window provides visualization
            pass

    def _get_state(self) -> Dict[str, Any]:
        """
        Get current game state from client.

        Returns:
            State dictionary
        """
        if self.client is None:
            raise RuntimeError("Client not initialized")

        # Get latest state from queue
        state = self.client.state_queue.get_latest()

        if state is None:
            # No state available yet, wait a bit
            time.sleep(0.1)
            state = self.client.state_queue.get(timeout=5.0)

        if state is None:
            raise RuntimeError("Failed to get state from RimWorld server")

        return state

    def _send_reset_command(self) -> bool:
        """
        Send RESET command to RimWorld server.

        Returns:
            True if successful
        """
        # TODO: Implement RESET command in protobuf protocol
        # For now, assume server handles reset externally
        logger.warning("RESET command not yet implemented in protocol")
        return True

    def _send_step_command(self, ticks: int = 60):
        """
        Send STEP command to advance simulation.

        Args:
            ticks: Number of ticks to advance
        """
        # TODO: Send STEP command via client
        # For now, sleep to simulate step
        time.sleep(ticks / 60.0)  # Approximate timing
