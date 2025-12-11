"""
Tests for Gymnasium Environment

Validates RimWorldEnv, spaces, and reward calculations.
"""

import unittest
from unittest.mock import MagicMock, patch

import gymnasium as gym
import numpy as np
from gym_env import ActionSpace, ObservationSpace, RewardCalculator, RimWorldEnv


class TestObservationSpace(unittest.TestCase):
    """Test observation space definition and extraction."""

    def test_create_space(self):
        """Test observation space creation."""
        space = ObservationSpace.create()

        self.assertIsInstance(space, gym.spaces.Dict)
        self.assertIn("global", space.spaces)
        self.assertIn("colonists", space.spaces)
        self.assertIn("mask", space.spaces)

        # Check shapes
        self.assertEqual(space.spaces["global"].shape, (10,))
        self.assertEqual(
            space.spaces["colonists"].shape,
            (ObservationSpace.MAX_COLONISTS, ObservationSpace.COLONIST_FEATURES),
        )
        self.assertEqual(space.spaces["mask"].shape, (ObservationSpace.MAX_COLONISTS,))

    def test_extract_observation_empty(self):
        """Test observation extraction with empty state."""
        state = {"colonists": [], "global_state": {}, "frame_id": 0}

        obs = ObservationSpace.extract_observation(state)

        self.assertIn("global", obs)
        self.assertIn("colonists", obs)
        self.assertIn("mask", obs)

        # Check mask is all zeros for empty state
        self.assertEqual(np.sum(obs["mask"]), 0)

    def test_extract_observation_with_colonists(self):
        """Test observation extraction with colonists."""
        state = {
            "frame_id": 1000,
            "colonists": [
                {
                    "id": "c1",
                    "health": 0.8,
                    "mood": 0.6,
                    "position": {"x": 100.0, "y": 50.0, "z": 0.0},
                    "current_job": "Haul",
                    "skills": [{"level": 10}, {"level": 8}],
                    "drafted": False,
                },
                {
                    "id": "c2",
                    "health": 0.3,
                    "mood": 0.4,
                    "position": {"x": 120.0, "y": 60.0, "z": 0.0},
                    "current_job": "None",
                    "skills": [],
                    "drafted": True,
                },
            ],
            "global_state": {"colonist_count": 2, "wealth": 5000},
        }

        obs = ObservationSpace.extract_observation(state)

        # Check mask
        self.assertEqual(np.sum(obs["mask"]), 2)
        self.assertEqual(obs["mask"][0], 1)
        self.assertEqual(obs["mask"][1], 1)

        # Check colonist features extracted
        self.assertAlmostEqual(obs["colonists"][0, 0], 0.8, places=2)  # health
        self.assertAlmostEqual(obs["colonists"][1, 0], 0.3, places=2)  # health

        # Check global features
        self.assertGreater(obs["global"][0], 0.0)  # normalized time

    def test_extract_colonist_features_complete(self):
        """Test colonist feature extraction with all fields."""
        colonist = {
            "id": "c1",
            "health": 0.9,
            "mood": 0.7,
            "hunger": 0.3,
            "rest": 0.8,
            "recreation": 0.5,
            "drafted": True,
            "position": {"x": 150.0, "y": 100.0, "z": 0.0},
            "current_job": "AttackMelee",
            "skills": [{"level": 15}, {"level": 12}, {"level": 8}],
            "needs": [{"value": 0.6}, {"value": 0.7}],
            "health_capacities": [{"efficiency": 0.95}, {"efficiency": 1.0}],
        }

        features = ObservationSpace._extract_colonist_features(colonist)

        self.assertEqual(len(features), ObservationSpace.COLONIST_FEATURES)
        self.assertAlmostEqual(features[0], 0.9, places=2)  # health
        self.assertAlmostEqual(features[1], 0.7, places=2)  # mood
        self.assertAlmostEqual(features[5], 1.0, places=2)  # drafted
        self.assertAlmostEqual(features[10], 1.0, places=2)  # dangerous job


class TestActionSpace(unittest.TestCase):
    """Test action space definition and decoding."""

    def test_create_space(self):
        """Test action space creation."""
        space = ActionSpace.create()

        self.assertIsInstance(space, gym.spaces.MultiDiscrete)
        self.assertEqual(len(space.nvec), 3)
        self.assertEqual(space.nvec[0], ActionSpace.MAX_COLONISTS)
        self.assertEqual(space.nvec[1], ActionSpace.ACTION_TYPES)
        self.assertEqual(space.nvec[2], ActionSpace.MAX_TARGETS)

    def test_decode_action_none(self):
        """Test decoding NONE action."""
        action = np.array([0, ActionSpace.ACTION_NONE, 0])
        state = {"colonists": [{"id": "c1"}]}

        result = ActionSpace.decode_action(action, state)
        self.assertIsNone(result)

    def test_decode_action_draft(self):
        """Test decoding DRAFT action."""
        action = np.array([0, ActionSpace.ACTION_DRAFT, 0])
        state = {"colonists": [{"id": "c1", "drafted": False}]}

        result = ActionSpace.decode_action(action, state)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "DRAFT_COLONIST")
        self.assertEqual(result["colonist_id"], "c1")
        self.assertEqual(result["source"], "policy")

    def test_decode_action_undraft(self):
        """Test decoding UNDRAFT action."""
        action = np.array([0, ActionSpace.ACTION_UNDRAFT, 0])
        state = {"colonists": [{"id": "c1", "drafted": True}]}

        result = ActionSpace.decode_action(action, state)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "UNDRAFT_COLONIST")

    def test_decode_action_rescue(self):
        """Test decoding RESCUE action."""
        action = np.array([0, ActionSpace.ACTION_RESCUE, 1])
        state = {
            "colonists": [
                {"id": "c1", "drafted": True},
                {"id": "c2", "health": 0.2},
            ]
        }

        result = ActionSpace.decode_action(action, state)

        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "RESCUE_COLONIST")
        self.assertEqual(result["colonist_id"], "c1")
        self.assertEqual(result["target_colonist_id"], "c2")

    def test_decode_action_invalid_colonist(self):
        """Test decoding with invalid colonist index."""
        action = np.array([10, ActionSpace.ACTION_DRAFT, 0])
        state = {"colonists": [{"id": "c1"}]}  # Only 1 colonist

        result = ActionSpace.decode_action(action, state)
        self.assertIsNone(result)

    def test_get_action_mask(self):
        """Test action mask generation."""
        state = {
            "colonists": [
                {"id": "c1", "drafted": False, "health": 1.0},
                {"id": "c2", "drafted": True, "health": 0.3},
            ]
        }

        mask = ActionSpace.get_action_mask(state)

        # Check shape
        self.assertEqual(
            mask.shape,
            (
                ActionSpace.MAX_COLONISTS,
                ActionSpace.ACTION_TYPES,
                ActionSpace.MAX_TARGETS,
            ),
        )

        # NONE always valid
        self.assertTrue(mask[0, ActionSpace.ACTION_NONE, 0])
        self.assertTrue(mask[1, ActionSpace.ACTION_NONE, 0])

        # First colonist not drafted -> can DRAFT
        self.assertTrue(mask[0, ActionSpace.ACTION_DRAFT, 0])
        self.assertFalse(mask[0, ActionSpace.ACTION_UNDRAFT, 0])

        # Second colonist drafted -> can UNDRAFT
        self.assertFalse(mask[1, ActionSpace.ACTION_DRAFT, 0])
        self.assertTrue(mask[1, ActionSpace.ACTION_UNDRAFT, 0])


class TestRewardCalculator(unittest.TestCase):
    """Test reward calculation logic."""

    def setUp(self):
        """Set up reward calculator for each test."""
        self.calculator = RewardCalculator()

    def test_initialization(self):
        """Test calculator initialization."""
        self.assertEqual(self.calculator.weight_survival, 10.0)
        self.assertEqual(self.calculator.penalty_death, -20.0)
        self.assertIsNone(self.calculator._previous_state)

    def test_custom_configuration(self):
        """Test calculator with custom config."""
        config = {
            "weight_survival": 5.0,
            "penalty_death": -30.0,
        }
        calculator = RewardCalculator(config=config)

        self.assertEqual(calculator.weight_survival, 5.0)
        self.assertEqual(calculator.penalty_death, -30.0)

    def test_first_step_zero_reward(self):
        """Test first step returns zero reward."""
        state = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}

        reward = self.calculator.compute_reward(state)
        self.assertEqual(reward, 0.0)

    def test_survival_reward_constant(self):
        """Test survival gives constant small reward."""
        state1 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}
        state2 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}

        self.calculator.compute_reward(state1)
        reward = self.calculator.compute_reward(state2)

        # Should get small positive reward for keeping colonist alive
        self.assertGreater(reward, 0.0)

    def test_death_penalty(self):
        """Test death incurs large penalty."""
        state1 = {
            "colonists": [
                {"id": "c1", "health": 1.0, "mood": 0.5},
                {"id": "c2", "health": 1.0, "mood": 0.5},
            ]
        }
        state2 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}

        self.calculator.compute_reward(state1)
        reward = self.calculator.compute_reward(state2)

        # Should get large negative reward for death
        self.assertLessEqual(reward, -10.0)

    def test_health_reward_good(self):
        """Test high health gives positive reward."""
        state1 = {"colonists": [{"id": "c1", "health": 0.9, "mood": 0.5}]}
        state2 = {"colonists": [{"id": "c1", "health": 0.9, "mood": 0.5}]}

        self.calculator.compute_reward(state1)
        reward = self.calculator.compute_reward(state2)

        # Health > 0.5 should contribute positive reward
        self.assertGreater(reward, 0.0)

    def test_health_reward_critical(self):
        """Test critical health gives penalty."""
        state1 = {"colonists": [{"id": "c1", "health": 0.15, "mood": 0.5}]}
        state2 = {"colonists": [{"id": "c1", "health": 0.15, "mood": 0.5}]}

        self.calculator.compute_reward(state1)
        reward = self.calculator.compute_reward(state2)

        # Critical health (<0.2) should incur penalty
        self.assertLess(reward, 0.0)

    def test_mood_reward(self):
        """Test mood affects reward."""
        state1 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.8}]}
        state2 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.8}]}

        self.calculator.compute_reward(state1)
        reward_high_mood = self.calculator.compute_reward(state2)

        # Reset for low mood test
        self.calculator.reset()
        state3 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.2}]}
        state4 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.2}]}

        self.calculator.compute_reward(state3)
        reward_low_mood = self.calculator.compute_reward(state4)

        # High mood should give better reward than low mood
        self.assertGreater(reward_high_mood, reward_low_mood)

    def test_terminal_reward_all_dead(self):
        """Test terminal state with all colonists dead."""
        state1 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}
        state2 = {"colonists": []}

        self.calculator.compute_reward(state1)
        reward = self.calculator.compute_reward(state2, done=True)

        # Should get penalty for all dead (terminal state)
        self.assertLessEqual(reward, -10.0)

    def test_terminal_reward_survival(self):
        """Test terminal state with colonists surviving."""
        state1 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}
        state2 = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}

        self.calculator.compute_reward(state1)
        reward = self.calculator.compute_reward(state2, done=True)

        # Should get bonus for surviving to end
        self.assertGreater(reward, 0.0)

    def test_reset(self):
        """Test calculator reset."""
        state = {"colonists": [{"id": "c1", "health": 1.0, "mood": 0.5}]}

        self.calculator.compute_reward(state)
        self.assertIsNotNone(self.calculator._previous_state)

        self.calculator.reset()
        self.assertIsNone(self.calculator._previous_state)


class TestRimWorldEnv(unittest.TestCase):
    """Test RimWorld Gymnasium environment."""

    @patch("gym_env.rimworld_env.SpectatorClient")
    def test_initialization(self, mock_client_class):
        """Test environment initialization."""
        env = RimWorldEnv(host="localhost", port=50051, training_mode=True)

        self.assertEqual(env.host, "localhost")
        self.assertEqual(env.port, 50051)
        self.assertTrue(env.training_mode)
        self.assertEqual(env.max_episode_steps, 10000)

        # Check spaces defined
        self.assertIsNotNone(env.observation_space)
        self.assertIsNotNone(env.action_space)
        self.assertIsNotNone(env.reward_calculator)

    @patch("gym_env.rimworld_env.SpectatorClient")
    def test_reset(self, mock_client_class):
        """Test environment reset."""
        # Mock client behavior
        mock_client = MagicMock()
        mock_client.wait_ready.return_value = True
        mock_client.state_queue.get_latest.return_value = {
            "colonists": [{"id": "c1", "health": 1.0, "position": {}}],
            "global_state": {},
            "frame_id": 0,
        }
        mock_client_class.return_value = mock_client

        env = RimWorldEnv()
        obs, info = env.reset()

        # Check observation structure
        self.assertIn("global", obs)
        self.assertIn("colonists", obs)
        self.assertIn("mask", obs)

        # Check info
        self.assertEqual(info["episode_step"], 0)
        self.assertEqual(info["episode_return"], 0.0)
        self.assertGreater(info["colonist_count"], 0)

        # Check client started
        mock_client.start.assert_called_once()
        mock_client.wait_ready.assert_called_once()

    @patch("gym_env.rimworld_env.SpectatorClient")
    def test_close(self, mock_client_class):
        """Test environment cleanup."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        env = RimWorldEnv()
        env.client = mock_client
        env.close()

        mock_client.stop.assert_called_once()
        self.assertIsNone(env.client)


if __name__ == "__main__":
    unittest.main()
