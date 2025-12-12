"""RimGym Gymnasium environment package.

Provides a standard RL environment interface compatible with Stable-Baselines3.
"""

from .rewards import RewardCalculator
from .rimworld_env import RimWorldEnv
from .spaces import ActionSpace, ObservationSpace

__all__ = [
    "RimWorldEnv",
    "ObservationSpace",
    "ActionSpace",
    "RewardCalculator",
]

__version__ = "0.3.0"
