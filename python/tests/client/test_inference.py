"""
Unit tests for InferenceThread and Policy system.

Tests Phase IV.3 components:
- Policy interface
- ExecutivePolicy implementation
- InferenceThread lifecycle and operation
"""

import os
import queue
import sys
import threading
import time
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from client.inference import InferenceThread
from client.queues import ActionQueue, StateQueue
from policies.executive import ExecutivePolicy
from policies.policy import Policy


class TestPolicyInterface(unittest.TestCase):
    """Test abstract Policy interface."""

    def test_policy_requires_decide_implementation(self):
        """Policy subclass must implement decide()."""
        with self.assertRaises(TypeError):
            # Cannot instantiate abstract class
            Policy(name="test")

    def test_policy_statistics_tracking(self):
        """Policy tracks decision and error counts."""

        class TestPolicy(Policy):
            def decide(self, state):
                self._record_decision()
                return [{"type": "TEST"}]

        policy = TestPolicy(name="test")

        # Initial stats
        stats = policy.get_stats()
        self.assertEqual(stats["decision_count"], 0)
        self.assertEqual(stats["error_count"], 0)

        # After decisions
        policy.decide({})
        policy.decide({})
        self._record_error_helper(policy)

        stats = policy.get_stats()
        self.assertEqual(stats["decision_count"], 2)
        self.assertEqual(stats["error_count"], 1)

    def _record_error_helper(self, policy):
        """Helper to record error."""
        policy._record_error()

    def test_policy_reset(self):
        """Reset clears policy statistics."""

        class TestPolicy(Policy):
            def decide(self, state):
                self._record_decision()
                return None

        policy = TestPolicy(name="test")
        policy.decide({})
        policy._record_error()

        # Reset
        policy.reset()

        stats = policy.get_stats()
        self.assertEqual(stats["decision_count"], 0)
        self.assertEqual(stats["error_count"], 0)


class TestExecutivePolicy(unittest.TestCase):
    """Test ExecutivePolicy implementation."""

    def test_initialization(self):
        """ExecutivePolicy initializes with default config."""
        policy = ExecutivePolicy()

        self.assertEqual(policy.name, "ExecutivePolicy")
        self.assertEqual(policy.health_critical, 0.3)
        self.assertEqual(policy.health_warning, 0.5)
        self.assertTrue(policy.auto_draft)
        self.assertTrue(policy.health_management)

    def test_custom_configuration(self):
        """ExecutivePolicy accepts custom config."""
        config = {
            "health_critical_threshold": 0.2,
            "health_warning_threshold": 0.4,
            "enable_auto_draft": False,
            "enable_health_management": False,
        }

        policy = ExecutivePolicy(config=config)

        self.assertEqual(policy.health_critical, 0.2)
        self.assertEqual(policy.health_warning, 0.4)
        self.assertFalse(policy.auto_draft)
        self.assertFalse(policy.health_management)

    def test_no_actions_for_healthy_colonists(self):
        """Policy returns None when all colonists are healthy."""
        policy = ExecutivePolicy()

        state = {
            "frame_id": 100,
            "colonists": [
                {"id": "1", "health": 1.0, "job": "Mining"},
                {"id": "2", "health": 0.8, "job": "Hauling"},
            ],
        }

        actions = policy.decide(state)
        self.assertIsNone(actions)

    def test_critical_health_generates_medical_action(self):
        """Policy generates SEND_TO_MEDICAL for critical health."""
        policy = ExecutivePolicy()

        state = {
            "frame_id": 100,
            "colonists": [
                {"id": "colonist_1", "health": 0.15, "job": "Mining"},  # Critical
            ],
        }

        actions = policy.decide(state)

        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "SEND_TO_MEDICAL")
        self.assertEqual(actions[0]["target"], "colonist_1")
        self.assertEqual(actions[0]["priority"], "CRITICAL")

    def test_warning_health_logged_but_no_action(self):
        """Policy logs warning health but doesn't generate action yet."""
        policy = ExecutivePolicy()

        state = {
            "frame_id": 100,
            "colonists": [
                {"id": "colonist_1", "health": 0.4, "job": "Mining"},  # Warning
            ],
        }

        actions = policy.decide(state)
        # Currently only critical health generates actions
        self.assertIsNone(actions)

    def test_no_duplicate_medical_action_if_already_in_medical(self):
        """Policy doesn't send to medical if already there."""
        policy = ExecutivePolicy()

        state = {
            "frame_id": 100,
            "colonists": [
                {"id": "colonist_1", "health": 0.15, "job": "PatientGoToBed"},
            ],
        }

        actions = policy.decide(state)
        self.assertIsNone(actions)  # Already in medical, no action

    def test_multiple_critical_colonists(self):
        """Policy handles multiple critical colonists."""
        policy = ExecutivePolicy()

        state = {
            "frame_id": 100,
            "colonists": [
                {"id": "colonist_1", "health": 0.15, "job": "Mining"},
                {"id": "colonist_2", "health": 0.25, "job": "Hauling"},
                {"id": "colonist_3", "health": 0.9, "job": "Growing"},
            ],
        }

        actions = policy.decide(state)

        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 2)  # Two critical colonists
        self.assertEqual(actions[0]["target"], "colonist_1")
        self.assertEqual(actions[1]["target"], "colonist_2")

    def test_health_management_disabled(self):
        """Policy respects health_management config."""
        config = {"enable_health_management": False}
        policy = ExecutivePolicy(config=config)

        state = {
            "frame_id": 100,
            "colonists": [
                {"id": "colonist_1", "health": 0.15, "job": "Mining"},
            ],
        }

        actions = policy.decide(state)
        self.assertIsNone(actions)  # Health management disabled

    def test_empty_colonist_list(self):
        """Policy handles empty colonist list."""
        policy = ExecutivePolicy()

        state = {"frame_id": 100, "colonists": []}

        actions = policy.decide(state)
        self.assertIsNone(actions)

    def test_policy_error_handling(self):
        """Policy handles malformed state gracefully."""
        policy = ExecutivePolicy()

        # Missing colonists key
        state = {"frame_id": 100}

        actions = policy.decide(state)
        self.assertIsNone(actions)  # Gracefully returns None

    def test_decision_counting(self):
        """Policy tracks successful decisions."""
        policy = ExecutivePolicy()

        state = {
            "frame_id": 100,
            "colonists": [{"id": "1", "health": 1.0, "job": "Mining"}],
        }

        policy.decide(state)
        policy.decide(state)

        stats = policy.get_stats()
        self.assertEqual(stats["decision_count"], 2)
        self.assertEqual(stats["error_count"], 0)


class TestInferenceThread(unittest.TestCase):
    """Test InferenceThread lifecycle and operation."""

    def setUp(self):
        """Set up test fixtures."""
        self.state_queue = StateQueue(maxsize=10)
        self.action_queue = ActionQueue(maxsize=100)
        self.stop_event = threading.Event()

        # Mock policy
        self.mock_policy = Mock(spec=Policy)
        self.mock_policy.name = "MockPolicy"
        self.mock_policy.get_stats.return_value = {
            "name": "MockPolicy",
            "decision_count": 0,
            "error_count": 0,
        }

    def test_initialization(self):
        """InferenceThread initializes correctly."""
        thread = InferenceThread(
            policy=self.mock_policy,
            state_queue=self.state_queue,
            action_queue=self.action_queue,
            stop_event=self.stop_event,
            timeout_ms=100,
        )

        self.assertEqual(thread.policy, self.mock_policy)
        self.assertEqual(thread.timeout_ms, 100)
        self.assertFalse(thread.is_alive())

    def test_thread_lifecycle(self):
        """InferenceThread starts and stops cleanly."""
        self.mock_policy.decide.return_value = None

        thread = InferenceThread(
            policy=self.mock_policy,
            state_queue=self.state_queue,
            action_queue=self.action_queue,
            stop_event=self.stop_event,
            timeout_ms=10,  # Shorter timeout for faster test
        )

        thread.start()
        self.assertTrue(thread.is_alive())

        time.sleep(0.05)  # Let it run briefly

        self.stop_event.set()
        thread.join(timeout=2.0)  # Longer join timeout for safety

        self.assertFalse(thread.is_alive())

    def test_state_consumption_and_policy_invocation(self):
        """InferenceThread consumes states and invokes policy."""
        state = {"frame_id": 100, "colonists": [{"id": "1", "health": 1.0}]}

        self.mock_policy.decide.return_value = None

        thread = InferenceThread(
            policy=self.mock_policy,
            state_queue=self.state_queue,
            action_queue=self.action_queue,
            stop_event=self.stop_event,
            timeout_ms=10,  # Shorter timeout for faster test
        )

        thread.start()

        # Put state in queue
        self.state_queue.put(state)

        time.sleep(0.05)  # Give time to process

        self.stop_event.set()
        thread.join(timeout=2.0)  # Longer join timeout

        # Verify policy was called
        self.mock_policy.decide.assert_called()

        stats = thread.get_stats()
        self.assertGreater(stats["states_processed"], 0)

    def test_action_generation_and_queuing(self):
        """InferenceThread queues actions from policy."""
        state = {"frame_id": 100, "colonists": []}

        actions = [
            {"type": "MOVE", "target": "pos1"},
            {"type": "ATTACK", "target": "enemy1"},
        ]

        self.mock_policy.decide.return_value = actions

        thread = InferenceThread(
            policy=self.mock_policy,
            state_queue=self.state_queue,
            action_queue=self.action_queue,
            stop_event=self.stop_event,
            timeout_ms=10,  # Shorter timeout
        )

        thread.start()
        self.state_queue.put(state)

        # Wait for actions to be queued (check before stopping thread)
        queued_actions = []
        deadline = time.time() + 1.0  # 1 second deadline
        while len(queued_actions) < 2 and time.time() < deadline:
            try:
                action = self.action_queue.get(timeout=0.01)
                queued_actions.append(action)
            except queue.Empty:
                pass

        # Now stop the thread
        self.stop_event.set()
        thread.join(timeout=2.0)

        self.assertEqual(len(queued_actions), 2)
        self.assertEqual(queued_actions[0]["type"], "MOVE")
        self.assertEqual(queued_actions[1]["type"], "ATTACK")

    def test_policy_error_handling(self):
        """InferenceThread handles policy errors gracefully."""
        state = {"frame_id": 100, "colonists": []}

        # Policy raises exception
        self.mock_policy.decide.side_effect = Exception("Policy error")

        thread = InferenceThread(
            policy=self.mock_policy,
            state_queue=self.state_queue,
            action_queue=self.action_queue,
            stop_event=self.stop_event,
            timeout_ms=10,  # Shorter timeout
        )

        thread.start()
        self.state_queue.put(state)

        time.sleep(0.05)  # Give time to process

        self.stop_event.set()
        thread.join(timeout=2.0)

        # Thread should still be running (didn't crash)
        stats = thread.get_stats()
        self.assertGreater(stats["policy_errors"], 0)

    def test_statistics_tracking(self):
        """InferenceThread tracks comprehensive statistics."""
        self.mock_policy.decide.return_value = [{"type": "TEST"}]

        thread = InferenceThread(
            policy=self.mock_policy,
            state_queue=self.state_queue,
            action_queue=self.action_queue,
            stop_event=self.stop_event,
            timeout_ms=10,  # Shorter timeout
        )

        thread.start()

        # Process multiple states
        for i in range(5):
            self.state_queue.put({"frame_id": i, "colonists": []})

        time.sleep(0.1)  # Give time to process

        self.stop_event.set()
        thread.join(timeout=2.0)

        stats = thread.get_stats()

        self.assertGreater(stats["states_processed"], 0)
        self.assertGreater(stats["actions_generated"], 0)
        self.assertEqual(stats["policy_errors"], 0)
        self.assertIn("avg_latency_ms", stats)


class TestInferenceIntegration(unittest.TestCase):
    """Integration tests for Inference thread with real policy."""

    def test_executive_policy_with_inference_thread(self):
        """Full integration: ExecutivePolicy + InferenceThread."""
        state_queue = StateQueue(maxsize=10)
        action_queue = ActionQueue(maxsize=100)
        stop_event = threading.Event()

        policy = ExecutivePolicy()

        thread = InferenceThread(
            policy=policy,
            state_queue=state_queue,
            action_queue=action_queue,
            stop_event=stop_event,
            timeout_ms=10,  # Shorter timeout for faster test
        )

        thread.start()

        # Send state with critical health colonist
        state = {
            "frame_id": 100,
            "colonists": [
                {"id": "colonist_1", "health": 0.15, "job": "Mining"},
            ],
        }

        state_queue.put(state)

        time.sleep(0.05)  # Allow processing

        stop_event.set()
        thread.join(timeout=2.0)

        # Check action was generated
        action = action_queue.get(timeout=0.1)

        self.assertEqual(action["type"], "SEND_TO_MEDICAL")
        self.assertEqual(action["target"], "colonist_1")

        stats = thread.get_stats()
        self.assertGreater(stats["states_processed"], 0)
        self.assertGreater(stats["actions_generated"], 0)


if __name__ == "__main__":
    unittest.main()
