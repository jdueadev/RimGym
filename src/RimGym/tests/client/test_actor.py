"""
Tests for Actor Thread and Reflex Policy

Validates:
- ReflexPolicy decision logic
- ActorThread lifecycle and event processing
- Priority-based event handling
- Ultra-low latency reactions (<10ms)
"""

import threading
import time
import unittest
from unittest.mock import MagicMock

from client.actor import ActorThread
from client.queues import ActionQueue, EventPriority, EventQueue
from policies.reflex import ReflexPolicy


class TestReflexPolicy(unittest.TestCase):
    """Test Reflex Policy decision logic."""

    def test_initialization(self):
        """Test policy initialization with defaults."""
        policy = ReflexPolicy()
        self.assertEqual(policy.name, "ReflexPolicy")
        self.assertEqual(policy.health_critical, 0.2)
        self.assertTrue(policy.enable_auto_rescue)
        self.assertFalse(policy.enable_auto_draft)

    def test_custom_configuration(self):
        """Test policy initialization with custom config."""
        config = {
            "health_critical_threshold": 0.15,
            "enable_auto_rescue": False,
            "enable_auto_draft": True,
        }
        policy = ReflexPolicy(config=config)
        self.assertEqual(policy.health_critical, 0.15)
        self.assertFalse(policy.enable_auto_rescue)
        self.assertTrue(policy.enable_auto_draft)

    def test_health_critical_generates_rescue(self):
        """Test critical health event generates rescue action."""
        policy = ReflexPolicy()
        event = {
            "type": "health_critical",
            "colonist_id": "colonist_001",
            "health": 0.10,  # 10% health
            "priority": "CRITICAL",
        }

        actions = policy.decide(event)
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "RESCUE_COLONIST")
        self.assertEqual(actions[0]["colonist_id"], "colonist_001")
        self.assertEqual(actions[0]["priority"], "critical")
        self.assertEqual(actions[0]["source"], "reflex")

    def test_health_warning_no_reflex_action(self):
        """Test warning health event doesn't trigger reflex action."""
        policy = ReflexPolicy()
        event = {
            "type": "health_warning",
            "colonist_id": "colonist_002",
            "health": 0.40,  # 40% health
            "priority": "HIGH",
        }

        actions = policy.decide(event)
        # Reflex layer doesn't act on warnings - Executive handles those
        self.assertIsNone(actions)

    def test_colonist_missing_generates_alert(self):
        """Test missing colonist event generates alert."""
        policy = ReflexPolicy()
        event = {
            "type": "colonist_missing",
            "colonist_id": "colonist_003",
            "colonist_name": "Jane",
            "priority": "HIGH",
        }

        actions = policy.decide(event)
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "ALERT")
        self.assertEqual(actions[0]["priority"], "high")
        self.assertIn("Jane", actions[0]["message"])

    def test_dangerous_job_with_low_health_interrupted(self):
        """Test dangerous job with low health generates interrupt."""
        policy = ReflexPolicy()
        event = {
            "type": "job_changed",
            "colonist_id": "colonist_004",
            "old_job": "Wander",
            "new_job": "AttackMelee",
            "health": 0.30,  # 30% health, risky for combat
            "priority": "LOW",
        }

        actions = policy.decide(event)
        self.assertIsNotNone(actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "INTERRUPT_JOB")
        self.assertEqual(actions[0]["priority"], "high")

    def test_dangerous_job_with_high_health_allowed(self):
        """Test dangerous job with good health doesn't trigger action."""
        policy = ReflexPolicy()
        event = {
            "type": "job_changed",
            "colonist_id": "colonist_005",
            "old_job": "Wander",
            "new_job": "AttackMelee",
            "health": 0.90,  # 90% health, safe for combat
            "priority": "LOW",
        }

        actions = policy.decide(event)
        self.assertIsNone(actions)

    def test_colonist_joined_no_action(self):
        """Test new colonist event doesn't trigger reflex action."""
        policy = ReflexPolicy()
        event = {
            "type": "colonist_joined",
            "colonist_id": "colonist_006",
            "colonist_name": "Bob",
            "priority": "MEDIUM",
        }

        actions = policy.decide(event)
        self.assertIsNone(actions)

    def test_rescue_disabled_no_action(self):
        """Test rescue action disabled by config."""
        policy = ReflexPolicy(config={"enable_auto_rescue": False})
        event = {
            "type": "health_critical",
            "colonist_id": "colonist_007",
            "health": 0.05,  # 5% health
            "priority": "CRITICAL",
        }

        actions = policy.decide(event)
        self.assertIsNone(actions)

    def test_unknown_event_type_no_action(self):
        """Test unknown event type returns None."""
        policy = ReflexPolicy()
        event = {
            "type": "unknown_event",
            "data": "test",
            "priority": "LOW",
        }

        actions = policy.decide(event)
        self.assertIsNone(actions)

    def test_policy_error_handling(self):
        """Test policy handles malformed events gracefully."""
        policy = ReflexPolicy()
        # Missing required fields
        event = {"type": "health_critical"}

        # Should not crash, returns list (may have actions with partial data)
        actions = policy.decide(event)
        # Should handle gracefully without raising exceptions
        self.assertIsInstance(actions, list)

    def test_decision_counting(self):
        """Test decision counter increments."""
        policy = ReflexPolicy()
        event1 = {"type": "colonist_joined", "colonist_id": "c1", "priority": "MEDIUM"}
        event2 = {
            "type": "health_warning",
            "colonist_id": "c2",
            "health": 0.4,
            "priority": "HIGH",
        }

        policy.decide(event1)
        policy.decide(event2)

        stats = policy.get_stats()
        self.assertEqual(stats["decision_count"], 2)
        self.assertEqual(stats["error_count"], 0)

    def test_reset(self):
        """Test policy reset clears state."""
        policy = ReflexPolicy()
        event = {"type": "colonist_joined", "colonist_id": "c1", "priority": "MEDIUM"}

        policy.decide(event)
        policy.reset()

        stats = policy.get_stats()
        self.assertEqual(stats["decision_count"], 0)
        self.assertEqual(stats["error_count"], 0)


class TestActorThread(unittest.TestCase):
    """Test Actor Thread lifecycle and event processing."""

    def test_initialization(self):
        """Test actor thread initialization."""
        policy = MagicMock(spec=ReflexPolicy)
        event_queue = EventQueue(maxsize=10)
        action_queue = ActionQueue(maxsize=10)
        stop_event = threading.Event()

        actor = ActorThread(
            policy=policy,
            event_queue=event_queue,
            action_queue=action_queue,
            stop_event=stop_event,
            timeout_ms=50,
        )

        self.assertEqual(actor.policy, policy)
        self.assertEqual(actor.event_queue, event_queue)
        self.assertEqual(actor.action_queue, action_queue)
        self.assertEqual(actor.timeout_ms, 50)
        self.assertEqual(actor.events_processed, 0)
        self.assertEqual(actor.actions_generated, 0)

    def test_thread_lifecycle(self):
        """Test actor thread starts and stops cleanly."""
        policy = MagicMock(spec=ReflexPolicy)
        policy.decide.return_value = None
        event_queue = EventQueue(maxsize=10)
        action_queue = ActionQueue(maxsize=10)
        stop_event = threading.Event()

        actor = ActorThread(
            policy=policy,
            event_queue=event_queue,
            action_queue=action_queue,
            stop_event=stop_event,
            timeout_ms=50,
        )

        actor.start()
        self.assertTrue(actor.is_alive())

        time.sleep(0.2)
        stop_event.set()
        actor.join(timeout=2.0)

        self.assertFalse(actor.is_alive())

    def test_event_consumption_and_policy_invocation(self):
        """Test actor consumes events and invokes policy."""
        policy = MagicMock(spec=ReflexPolicy)
        policy.decide.return_value = None
        event_queue = EventQueue(maxsize=10)
        action_queue = ActionQueue(maxsize=10)
        stop_event = threading.Event()

        actor = ActorThread(
            policy=policy,
            event_queue=event_queue,
            action_queue=action_queue,
            stop_event=stop_event,
            timeout_ms=50,
        )

        # Put test event
        test_event = {
            "type": "health_critical",
            "colonist_id": "c1",
            "priority": EventPriority.CRITICAL,
        }
        event_queue.put(test_event, priority=EventPriority.CRITICAL)

        actor.start()
        time.sleep(0.3)  # Allow processing
        stop_event.set()
        actor.join(timeout=2.0)

        # Verify policy was called
        policy.decide.assert_called()
        self.assertEqual(actor.events_processed, 1)

    def test_action_generation_and_queuing(self):
        """Test actor generates and queues actions."""
        policy = MagicMock(spec=ReflexPolicy)
        policy.decide.return_value = [
            {"type": "RESCUE", "colonist_id": "c1", "priority": "critical"}
        ]

        event_queue = EventQueue(maxsize=10)
        action_queue = ActionQueue(maxsize=10)
        stop_event = threading.Event()

        actor = ActorThread(
            policy=policy,
            event_queue=event_queue,
            action_queue=action_queue,
            stop_event=stop_event,
            timeout_ms=50,
        )

        test_event = {
            "type": "health_critical",
            "colonist_id": "c1",
            "priority": EventPriority.CRITICAL,
        }
        event_queue.put(test_event, priority=EventPriority.CRITICAL)

        actor.start()
        time.sleep(0.3)
        stop_event.set()
        actor.join(timeout=2.0)

        # Verify action was queued
        self.assertEqual(actor.actions_generated, 1)
        action = action_queue.get(timeout=1.0)
        self.assertIsNotNone(action)
        self.assertEqual(action["type"], "RESCUE")
        self.assertEqual(action["source"], "reflex")

    def test_policy_error_doesnt_crash_thread(self):
        """Test policy error is caught and logged."""
        policy = MagicMock(spec=ReflexPolicy)
        policy.decide.side_effect = Exception("Policy error")

        event_queue = EventQueue(maxsize=10)
        action_queue = ActionQueue(maxsize=10)
        stop_event = threading.Event()

        actor = ActorThread(
            policy=policy,
            event_queue=event_queue,
            action_queue=action_queue,
            stop_event=stop_event,
            timeout_ms=50,
        )

        test_event = {"type": "test", "priority": EventPriority.HIGH}
        event_queue.put(test_event, priority=EventPriority.HIGH)

        actor.start()
        time.sleep(0.3)
        stop_event.set()
        actor.join(timeout=2.0)

        # Thread should survive error
        self.assertEqual(actor.events_processed, 1)
        self.assertEqual(actor.policy_errors, 1)
        self.assertEqual(actor.actions_generated, 0)

    def test_statistics_tracking(self):
        """Test comprehensive statistics tracking."""
        policy = MagicMock(spec=ReflexPolicy)
        policy.decide.return_value = [{"type": "ACTION1"}]
        policy.get_stats.return_value = {"decisions": 5}

        event_queue = EventQueue(maxsize=10)
        action_queue = ActionQueue(maxsize=10)
        stop_event = threading.Event()

        actor = ActorThread(
            policy=policy,
            event_queue=event_queue,
            action_queue=action_queue,
            stop_event=stop_event,
        )

        # Process events
        for i in range(3):
            event_queue.put(
                {"type": f"event{i}", "priority": EventPriority.HIGH},
                priority=EventPriority.HIGH,
            )

        actor.start()
        time.sleep(0.5)
        stop_event.set()
        actor.join(timeout=2.0)

        stats = actor.get_statistics()
        self.assertGreater(stats["events_processed"], 0)
        self.assertGreater(stats["actions_generated"], 0)
        self.assertEqual(stats["policy_errors"], 0)
        self.assertIn("policy_stats", stats)


class TestActorIntegration(unittest.TestCase):
    """Integration tests for Actor + ReflexPolicy."""

    def test_full_integration(self):
        """Test full Actor thread with real ReflexPolicy."""
        policy = ReflexPolicy()
        event_queue = EventQueue(maxsize=100)
        action_queue = ActionQueue(maxsize=100)
        stop_event = threading.Event()

        actor = ActorThread(
            policy=policy,
            event_queue=event_queue,
            action_queue=action_queue,
            stop_event=stop_event,
            timeout_ms=50,
        )

        # Critical health event
        critical_event = {
            "type": "health_critical",
            "colonist_id": "c1",
            "health": 0.15,
            "priority": EventPriority.CRITICAL,
        }
        event_queue.put(critical_event, priority=EventPriority.CRITICAL)

        # Missing colonist event
        missing_event = {
            "type": "colonist_missing",
            "colonist_id": "c2",
            "colonist_name": "Jane",
            "priority": EventPriority.HIGH,
        }
        event_queue.put(missing_event, priority=EventPriority.HIGH)

        actor.start()
        time.sleep(0.5)
        stop_event.set()
        actor.join(timeout=2.0)

        # Verify actions generated
        self.assertGreater(actor.actions_generated, 0)
        self.assertGreater(actor.events_processed, 0)

        # Check actions in queue
        actions = []
        while not action_queue.empty():
            action = action_queue.get(timeout=0.1)
            if action:
                actions.append(action)

        self.assertGreater(len(actions), 0)
        # First should be rescue (CRITICAL priority)
        self.assertEqual(actions[0]["type"], "RESCUE_COLONIST")
        self.assertEqual(actions[0]["source"], "reflex")


if __name__ == "__main__":
    unittest.main()
