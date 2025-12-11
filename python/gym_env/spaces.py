"""
Space Definitions for RimWorld Gymnasium Environment

Defines observation and action spaces for RL algorithms.
"""

from typing import Any, Dict

import gymnasium as gym
import numpy as np


class ObservationSpace:
    """
    Observation space for RimWorld environment.

    Provides structured state representation suitable for RL algorithms.
    Uses Dict space with multiple components:
    - global: Global game state (time, threats, resources)
    - colonists: Array of colonist features (health, needs, skills, position)
    - spatial: Optional spatial map representation (future)
    """

    # Colonist feature dimensions
    COLONIST_FEATURES = 32  # health, needs, position, job, skills
    MAX_COLONISTS = 20  # Maximum colonists to track

    @staticmethod
    def create() -> gym.spaces.Dict:
        """
        Create observation space.

        Returns:
            Gymnasium Dict space with structured observation components
        """
        return gym.spaces.Dict(
            {
                "global": gym.spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(10,),  # Global features: time, resources, threats, etc.
                    dtype=np.float32,
                ),
                "colonists": gym.spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(
                        ObservationSpace.MAX_COLONISTS,
                        ObservationSpace.COLONIST_FEATURES,
                    ),
                    dtype=np.float32,
                ),
                "mask": gym.spaces.Box(
                    low=0,
                    high=1,
                    shape=(ObservationSpace.MAX_COLONISTS,),
                    dtype=np.int8,
                ),  # Mask for valid colonists (1=valid, 0=padding)
            }
        )

    @staticmethod
    def extract_observation(state: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Extract observation from RimWorld state.

        Args:
            state: State dict from RimWorld server

        Returns:
            Observation dict matching space definition
        """
        # Extract global features
        global_state = state.get("global_state", {})
        global_features = np.array(
            [
                state.get("frame_id", 0) / 1000.0,  # Normalized time
                global_state.get("colonist_count", 0) / 20.0,  # Normalized count
                global_state.get("wealth", 0) / 10000.0,  # Normalized wealth
                global_state.get("temperature", 20.0) / 50.0,  # Normalized temp
                0.0,  # Threat level (future)
                0.0,  # Food reserve (future)
                0.0,  # Medicine reserve (future)
                0.0,  # Mood average (future)
                0.0,  # Research progress (future)
                0.0,  # Reserved
            ],
            dtype=np.float32,
        )

        # Extract colonist features
        colonists_data = state.get("colonists", [])
        num_colonists = min(len(colonists_data), ObservationSpace.MAX_COLONISTS)

        colonists_features = np.zeros(
            (ObservationSpace.MAX_COLONISTS, ObservationSpace.COLONIST_FEATURES),
            dtype=np.float32,
        )

        mask = np.zeros(ObservationSpace.MAX_COLONISTS, dtype=np.int8)

        for i, colonist in enumerate(colonists_data[:num_colonists]):
            colonists_features[i] = ObservationSpace._extract_colonist_features(
                colonist
            )
            mask[i] = 1

        return {
            "global": global_features,
            "colonists": colonists_features,
            "mask": mask,
        }

    @staticmethod
    def _extract_colonist_features(colonist: Dict[str, Any]) -> np.ndarray:
        """
        Extract feature vector from single colonist.

        Args:
            colonist: Colonist data dict

        Returns:
            Feature vector (32 dimensions)
        """
        features = np.zeros(ObservationSpace.COLONIST_FEATURES, dtype=np.float32)

        # Basic stats (indices 0-5)
        features[0] = colonist.get("health", 1.0)
        features[1] = colonist.get("mood", 0.5)
        features[2] = colonist.get("hunger", 0.5) if "hunger" in colonist else 0.5
        features[3] = colonist.get("rest", 0.5) if "rest" in colonist else 0.5
        features[4] = (
            colonist.get("recreation", 0.5) if "recreation" in colonist else 0.5
        )
        features[5] = colonist.get("drafted", 0.0)

        # Position (indices 6-8)
        position = colonist.get("position", {})
        features[6] = position.get("x", 0.0) / 250.0  # Normalized to map size
        features[7] = position.get("y", 0.0) / 250.0
        features[8] = position.get("z", 0.0)

        # Job status (indices 9-10)
        current_job = colonist.get("current_job", "None")
        features[9] = 1.0 if current_job != "None" else 0.0
        features[10] = (
            1.0 if current_job in ["AttackMelee", "AttackStatic", "Hunt"] else 0.0
        )

        # Skills (indices 11-20) - sample top 10 skills
        skills = colonist.get("skills", [])
        for i, skill in enumerate(skills[:10]):
            features[11 + i] = skill.get("level", 0) / 20.0  # Normalized

        # Needs (indices 21-25) - additional needs
        needs = colonist.get("needs", [])
        for i, need in enumerate(needs[:5]):
            features[21 + i] = need.get("value", 0.5)

        # Health capacities (indices 26-31)
        capacities = colonist.get("health_capacities", [])
        for i, capacity in enumerate(capacities[:6]):
            features[26 + i] = capacity.get("efficiency", 1.0)

        return features


class ActionSpace:
    """
    Action space for RimWorld environment.

    Defines discrete actions available to RL agent.
    Uses MultiDiscrete for: [colonist_id, action_type, target_id]
    """

    MAX_COLONISTS = 20
    ACTION_TYPES = 8  # DRAFT, UNDRAFT, MOVE, ATTACK, RESCUE, HAUL, BUILD, NONE
    MAX_TARGETS = 50  # Maximum targets for actions

    # Action type enumeration
    ACTION_NONE = 0
    ACTION_DRAFT = 1
    ACTION_UNDRAFT = 2
    ACTION_MOVE = 3
    ACTION_ATTACK = 4
    ACTION_RESCUE = 5
    ACTION_HAUL = 6
    ACTION_BUILD = 7

    @staticmethod
    def create() -> gym.spaces.MultiDiscrete:
        """
        Create action space.

        Returns:
            Gymnasium MultiDiscrete space: [colonist_id, action_type, target_id]
        """
        return gym.spaces.MultiDiscrete(
            [
                ActionSpace.MAX_COLONISTS,  # Which colonist
                ActionSpace.ACTION_TYPES,  # What action
                ActionSpace.MAX_TARGETS,  # Target (if applicable)
            ]
        )

    @staticmethod
    def decode_action(action: np.ndarray, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode RL action to RimWorld command.

        Args:
            action: Action array [colonist_id, action_type, target_id]
            state: Current game state for validation

        Returns:
            Action dict for RimWorld or None if invalid
        """
        colonist_idx, action_type, target_idx = action

        # Get colonists list
        colonists = state.get("colonists", [])
        if colonist_idx >= len(colonists):
            return None  # Invalid colonist

        colonist = colonists[colonist_idx]
        colonist_id = colonist.get("id")

        # Map action type to command
        if action_type == ActionSpace.ACTION_NONE:
            return None
        elif action_type == ActionSpace.ACTION_DRAFT:
            return {
                "type": "DRAFT_COLONIST",
                "colonist_id": colonist_id,
                "source": "policy",
            }
        elif action_type == ActionSpace.ACTION_UNDRAFT:
            return {
                "type": "UNDRAFT_COLONIST",
                "colonist_id": colonist_id,
                "source": "policy",
            }
        elif action_type == ActionSpace.ACTION_MOVE:
            # target_idx maps to a predefined location or uses grid coordinates
            # Phase VI: Full position mapping requires pathfinding integration
            return {
                "type": "MOVE_COLONIST",
                "colonist_id": colonist_id,
                "target_idx": int(target_idx),
                "source": "policy",
            }
        elif action_type == ActionSpace.ACTION_ATTACK:
            return {
                "type": "ATTACK_TARGET",
                "colonist_id": colonist_id,
                "target_idx": int(target_idx),
                "source": "policy",
            }
        elif action_type == ActionSpace.ACTION_RESCUE:
            # Find injured colonist
            if target_idx < len(colonists):
                target_colonist = colonists[target_idx]
                return {
                    "type": "RESCUE_COLONIST",
                    "colonist_id": colonist_id,
                    "target_colonist_id": target_colonist.get("id"),
                    "source": "policy",
                }
            return None
        elif action_type == ActionSpace.ACTION_HAUL:
            return {
                "type": "HAUL_ITEM",
                "colonist_id": colonist_id,
                "target_idx": int(target_idx),
                "source": "policy",
            }
        elif action_type == ActionSpace.ACTION_BUILD:
            return {
                "type": "BUILD",
                "colonist_id": colonist_id,
                "target_idx": int(target_idx),
                "source": "policy",
            }

        return None

    @staticmethod
    def get_action_mask(state: Dict[str, Any]) -> np.ndarray:
        """
        Get mask of valid actions for current state.

        Args:
            state: Current game state

        Returns:
            Boolean mask array indicating valid actions
        """
        colonists = state.get("colonists", [])
        num_colonists = len(colonists)

        # Create mask for all action combinations
        mask = np.zeros(
            (
                ActionSpace.MAX_COLONISTS,
                ActionSpace.ACTION_TYPES,
                ActionSpace.MAX_TARGETS,
            ),
            dtype=bool,
        )

        # Valid colonists can take actions
        for i in range(min(num_colonists, ActionSpace.MAX_COLONISTS)):
            colonist = colonists[i]
            drafted = colonist.get("drafted", False)

            # NONE action always valid
            mask[i, ActionSpace.ACTION_NONE, :] = True

            # DRAFT/UNDRAFT based on current state
            if drafted:
                mask[i, ActionSpace.ACTION_UNDRAFT, :] = True
            else:
                mask[i, ActionSpace.ACTION_DRAFT, :] = True

            # Other actions valid if drafted
            if drafted:
                mask[i, ActionSpace.ACTION_MOVE, :] = True
                mask[i, ActionSpace.ACTION_ATTACK, :] = True

            # RESCUE valid if another colonist is injured
            for j in range(num_colonists):
                if i != j and colonists[j].get("health", 1.0) < 0.5:
                    mask[i, ActionSpace.ACTION_RESCUE, j] = True

        return mask
