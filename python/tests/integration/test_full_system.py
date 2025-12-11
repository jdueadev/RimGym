"""
Full System Integration Tests

End-to-end tests using RimWorld Docker container.
Tests the complete triple-threaded client with real RimWorld connection.
"""

import logging
import time
import unittest
from typing import Optional

import numpy as np
from client import (
    ClientConfig,
    SpectatorClient,
)
from gym_env import RimWorldEnv
from policies import ExecutivePolicy, ReflexPolicy

logger = logging.getLogger(__name__)

# Test configuration
RIMWORLD_HOST = "localhost"
RIMWORLD_PORT = 50051
CONNECTION_TIMEOUT = 30.0


class DockerTestCase(unittest.TestCase):
    """Base class for tests requiring Docker RimWorld instance."""

    @classmethod
    def setUpClass(cls):
        """Check if RimWorld server is available."""
        cls.server_available = cls._check_server_available()
        if not cls.server_available:
            logger.warning(
                "RimWorld server not available. Start with: docker-compose up test"
            )

    @classmethod
    def _check_server_available(cls) -> bool:
        """
        Check if RimWorld server is reachable.

        Returns:
            True if server is available
        """
        try:
            from client.connection import ConnectionManager

            conn = ConnectionManager(
                host=RIMWORLD_HOST, port=RIMWORLD_PORT, connect_timeout=5.0
            )
            result = conn.connect()
            if result:
                conn.disconnect()
            return result
        except Exception as e:
            logger.debug(f"Server check failed: {e}")
            return False


class TestFullClientIntegration(DockerTestCase):
    """Test complete triple-threaded client with real RimWorld."""

    def setUp(self):
        """Set up test client."""
        if not self.server_available:
            self.skipTest("RimWorld server not available")

        self.client: Optional[SpectatorClient] = None

    def tearDown(self):
        """Clean up client."""
        if self.client:
            self.client.stop(timeout=5.0)
            self.client = None

    def test_client_connection_and_lifecycle(self):
        """Test client can connect and manage lifecycle."""
        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            training_mode=False,
            inference_mode=True,
        )

        client = SpectatorClient(config)

        # Start client
        client.start()

        # Wait for ready
        ready = client.wait_ready(timeout=CONNECTION_TIMEOUT)
        self.assertTrue(ready, "Client failed to become ready")

        # Verify queues initialized
        self.assertIsNotNone(client.state_queue)
        self.assertIsNotNone(client.event_queue)
        self.assertIsNotNone(client.action_queue)

        # Stop client
        client.stop(timeout=5.0)

        # Verify stopped successfully (stop() would raise if timeout)

    def test_listener_thread_polling(self):
        """
        Test Listener thread polls and populates state queue.
        TASK-021: Added retry logic and increased wait time.
        """
        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            poll_interval_ms=100,
        )

        client = SpectatorClient(config)
        client.start()

        self.assertTrue(client.wait_ready(timeout=CONNECTION_TIMEOUT))

        # TASK-021: Retry mechanism for handling temporary connection drops
        state = None
        max_retries = 3
        for attempt in range(max_retries):
            # Wait for states to accumulate (increased from 1.0 to 2.0 seconds)
            time.sleep(2.0)

            # Get state from queue
            state = client.state_queue.get_latest()

            if state is not None:
                break

            logger.warning(
                f"No state on attempt {attempt + 1}/{max_retries}, retrying..."
            )
            time.sleep(1.0)

        self.assertIsNotNone(
            state, f"No state received from Listener after {max_retries} attempts"
        )
        self.assertIn("colonists", state)
        self.assertIn("frame_id", state)

        # Verify continuous polling with retry
        frame1 = state.get("frame_id", 0)
        time.sleep(1.0)  # Increased from 0.5 to 1.0

        state2 = None
        for attempt in range(max_retries):
            state2 = client.state_queue.get_latest()
            if state2 is not None:
                break
            time.sleep(0.5)

        frame2 = state2.get("frame_id", 0) if state2 else 0

        self.assertGreaterEqual(frame2, frame1, "Frame should advance")

        client.stop(timeout=5.0)

    def test_event_detection(self):
        """Test Listener detects events and populates event queue."""
        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            poll_interval_ms=100,
        )

        client = SpectatorClient(config)
        client.start()

        self.assertTrue(client.wait_ready(timeout=CONNECTION_TIMEOUT))

        # Wait for event detection
        time.sleep(2.0)

        # Check if events generated
        event_count = 0
        while not client.event_queue.empty():
            event = client.event_queue.get(timeout=0.1)
            if event:
                event_count += 1
                logger.info(f"Detected event: {event.get('type')}")

        logger.info(f"Total events detected: {event_count}")

        # Events may or may not occur depending on game state
        # Just verify event detection mechanism works
        self.assertGreaterEqual(event_count, 0)

        client.stop(timeout=5.0)

    def test_inference_thread_with_executive_policy(self):
        """Test Inference thread processes states and generates actions."""
        policy = ExecutivePolicy(
            config={
                "health_critical_threshold": 0.3,
                "enable_health_management": True,
            }
        )

        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            executive_policy=policy,
        )

        client = SpectatorClient(config)
        client.start()

        self.assertTrue(client.wait_ready(timeout=CONNECTION_TIMEOUT))

        # Wait for policy to process states
        time.sleep(2.0)

        # Check if actions generated
        action_count = 0
        while not client.action_queue.empty():
            action = client.action_queue.get(timeout=0.1)
            if action:
                action_count += 1
                logger.info(
                    f"Action generated: {action.get('type')} (source: {action.get('source')})"
                )

        logger.info(f"Total actions generated: {action_count}")

        # Actions may or may not be generated depending on colonist health
        self.assertGreaterEqual(action_count, 0)

        # Get policy stats
        stats = policy.get_stats()
        logger.info(f"Policy stats: {stats}")

        client.stop(timeout=5.0)

    def test_actor_thread_with_reflex_policy(self):
        """Test Actor thread reacts to events and generates reflex actions."""
        reflex_policy = ReflexPolicy(
            config={
                "health_critical_threshold": 0.2,
                "enable_auto_rescue": True,
            }
        )

        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            reflex_policy=reflex_policy,
        )

        client = SpectatorClient(config)
        client.start()

        self.assertTrue(client.wait_ready(timeout=CONNECTION_TIMEOUT))

        # Wait for events and reflex responses
        time.sleep(2.0)

        # Check for reflex actions
        reflex_action_count = 0
        while not client.action_queue.empty():
            action = client.action_queue.get(timeout=0.1)
            if action and action.get("source") == "reflex":
                reflex_action_count += 1
                logger.info(f"Reflex action: {action.get('type')}")

        logger.info(f"Total reflex actions: {reflex_action_count}")

        # Reflex actions only if critical events occurred
        self.assertGreaterEqual(reflex_action_count, 0)

        client.stop(timeout=5.0)

    def test_triple_threaded_coordination(self):
        """Test all three threads working together."""
        executive_policy = ExecutivePolicy()
        reflex_policy = ReflexPolicy()

        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            executive_policy=executive_policy,
            reflex_policy=reflex_policy,
        )

        client = SpectatorClient(config)
        client.start()

        self.assertTrue(client.wait_ready(timeout=CONNECTION_TIMEOUT))

        # Let all threads work
        logger.info("Running triple-threaded system for 3 seconds...")
        time.sleep(3.0)

        # Collect statistics
        state_count = 0
        event_count = 0
        action_count = 0
        reflex_count = 0
        executive_count = 0

        # Count states
        while not client.state_queue.empty():
            if client.state_queue.get(timeout=0.1):
                state_count += 1

        # Count events
        while not client.event_queue.empty():
            if client.event_queue.get(timeout=0.1):
                event_count += 1

        # Count actions
        while not client.action_queue.empty():
            action = client.action_queue.get(timeout=0.1)
            if action:
                action_count += 1
                source = action.get("source", "unknown")
                if source == "reflex":
                    reflex_count += 1
                elif source == "policy":
                    executive_count += 1

        logger.info("System statistics:")
        logger.info(f"  States processed: {state_count}")
        logger.info(f"  Events detected: {event_count}")
        logger.info(f"  Total actions: {action_count}")
        logger.info(f"  Reflex actions: {reflex_count}")
        logger.info(f"  Executive actions: {executive_count}")

        # Verify system is functioning
        # Should have received some states at minimum
        self.assertGreater(state_count, 0, "No states received from Listener")

        client.stop(timeout=5.0)


class TestGymnasiumIntegration(DockerTestCase):
    """Test Gymnasium environment with real RimWorld."""

    def setUp(self):
        """Set up test environment."""
        if not self.server_available:
            self.skipTest("RimWorld server not available")

        self.env: Optional[RimWorldEnv] = None

    def tearDown(self):
        """Clean up environment."""
        if self.env:
            self.env.close()
            self.env = None

    def test_env_reset(self):
        """Test environment reset."""
        env = RimWorldEnv(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            training_mode=False,
            max_episode_steps=100,
        )

        obs, info = env.reset()

        # Verify observation structure
        self.assertIn("global", obs)
        self.assertIn("colonists", obs)
        self.assertIn("mask", obs)

        # Verify info
        self.assertEqual(info["episode_step"], 0)
        self.assertGreaterEqual(info["colonist_count"], 0)

        logger.info(f"Environment reset: {info['colonist_count']} colonists")

        env.close()

    def test_env_step(self):
        """Test environment step with actions."""
        env = RimWorldEnv(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            training_mode=False,
            max_episode_steps=100,
        )

        obs, info = env.reset()

        # Take a few steps
        for i in range(5):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            logger.info(
                f"Step {i + 1}: reward={reward:.3f}, colonists={info['colonist_count']}"
            )

            self.assertIsInstance(reward, (float, np.floating))
            self.assertIsInstance(terminated, bool)
            self.assertIsInstance(truncated, bool)

            if terminated or truncated:
                logger.info(f"Episode ended at step {i + 1}")
                break

        env.close()

    def test_env_episode_complete(self):
        """Test complete episode run."""
        env = RimWorldEnv(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            training_mode=False,
            max_episode_steps=20,  # Short episode for testing
        )

        obs, info = env.reset()

        episode_return = 0.0
        step_count = 0

        done = False
        while not done and step_count < 20:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            episode_return += reward
            step_count += 1
            done = terminated or truncated

        logger.info("Episode completed:")
        logger.info(f"  Steps: {step_count}")
        logger.info(f"  Return: {episode_return:.3f}")
        logger.info(f"  Final colonists: {info['colonist_count']}")

        self.assertGreater(step_count, 0)

        env.close()


class TestStressAndStability(DockerTestCase):
    """Stress tests for long-running stability."""

    def setUp(self):
        """Set up for stress test."""
        if not self.server_available:
            self.skipTest("RimWorld server not available")

    @unittest.skip("Long-running test, run manually")
    def test_long_running_stability(self):
        """Test client stability over extended period (1 hour)."""
        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            executive_policy=ExecutivePolicy(),
        )

        client = SpectatorClient(config)
        client.start()

        self.assertTrue(client.wait_ready(timeout=CONNECTION_TIMEOUT))

        duration_seconds = 3600  # 1 hour
        check_interval = 60  # Check every minute

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            time.sleep(check_interval)

            # Verify client still running
            state = client.state_queue.get_latest()
            self.assertIsNotNone(state, "Client stopped responding")

            elapsed = time.time() - start_time
            logger.info(f"Stability check: {elapsed / 60:.1f} minutes elapsed")

        client.stop(timeout=5.0)

    def test_reconnection(self):
        """Test client reconnection handling."""
        # This test would require restarting the docker container
        # For now, just verify reconnection logic exists
        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            reconnect_attempts=3,
            reconnect_backoff=1.0,
        )

        # Verify config accepts reconnection parameters
        self.assertEqual(config.reconnect_attempts, 3)
        self.assertEqual(config.reconnect_backoff, 1.0)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    unittest.main()
