"""
Performance Benchmarks

Validates performance targets for all components.
"""

import logging
import time
import unittest
from typing import List

import numpy as np
from client import ClientConfig, SpectatorClient
from policies import ExecutivePolicy, ReflexPolicy

logger = logging.getLogger(__name__)

# Test configuration
RIMWORLD_HOST = "localhost"
RIMWORLD_PORT = 50051
CONNECTION_TIMEOUT = 30.0


class PerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks for Phase IV components."""

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
        """Check if RimWorld server is reachable."""
        try:
            from client.connection import ConnectionManager

            conn = ConnectionManager(host=RIMWORLD_HOST, port=RIMWORLD_PORT)
            result = conn.connect(timeout=5.0)
            if result:
                conn.disconnect()
            return result
        except Exception:
            return False

    def setUp(self):
        """Set up for benchmark."""
        if not self.server_available:
            self.skipTest("RimWorld server not available")

    def test_listener_polling_throughput(self):
        """
        Benchmark: Listener polling throughput.

        Target: >10 polls/second
        """
        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            poll_interval_ms=100,  # 100ms = 10 polls/sec theoretical
        )

        client = SpectatorClient(config)
        client.start()
        client.wait_ready(timeout=CONNECTION_TIMEOUT)

        # Measure polls over 5 seconds
        initial_count = 0
        time.sleep(0.5)  # Warm up

        start_time = time.time()
        while not client.state_queue.empty():
            if client.state_queue.get(timeout=0.01):
                initial_count += 1

        # Run for 5 seconds
        time.sleep(5.0)

        elapsed = time.time() - start_time
        poll_count = 0
        while not client.state_queue.empty():
            if client.state_queue.get(timeout=0.01):
                poll_count += 1

        polls_per_second = poll_count / elapsed

        logger.info(f"Listener polling: {polls_per_second:.1f} polls/second")

        client.stop(timeout=5.0)

        # Verify target met
        self.assertGreater(
            polls_per_second, 10.0, f"Polling too slow: {polls_per_second:.1f}/sec"
        )

    def test_inference_latency(self):
        """
        Benchmark: Inference thread latency.

        Target: <100ms per decision
        """
        policy = ExecutivePolicy()

        config = ClientConfig(
            host=RIMWORLD_HOST,
            port=RIMWORLD_PORT,
            inference_mode=True,
            executive_policy=policy,
        )

        client = SpectatorClient(config)
        client.start()
        client.wait_ready(timeout=CONNECTION_TIMEOUT)

        # Collect decision latencies
        latencies: List[float] = []

        # Run for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10.0:
            state = client.state_queue.get(timeout=1.0)
            if state:
                decision_start = time.time()
                actions = policy.decide(state)
                decision_end = time.time()

                latency_ms = (decision_end - decision_start) * 1000
                latencies.append(latency_ms)

        if not latencies:
            self.skipTest("No policy decisions to measure")

        # Calculate statistics
        avg_latency = np.mean(latencies)
        p50_latency = np.percentile(latencies, 50)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        max_latency = np.max(latencies)

        logger.info("Inference latency (ms):")
        logger.info(f"  Average: {avg_latency:.2f}")
        logger.info(f"  P50: {p50_latency:.2f}")
        logger.info(f"  P95: {p95_latency:.2f}")
        logger.info(f"  P99: {p99_latency:.2f}")
        logger.info(f"  Max: {max_latency:.2f}")

        client.stop(timeout=5.0)

        # Verify target met
        self.assertLess(
            p95_latency, 100.0, f"Inference too slow: P95={p95_latency:.2f}ms"
        )

    def test_actor_reflex_latency(self):
        """
        Benchmark: Actor thread reflex latency.

        Target: <10ms per reaction
        """
        policy = ReflexPolicy()

        # Measure policy decision time directly
        latencies: List[float] = []

        # Create test events
        test_events = [
            {
                "type": "health_critical",
                "colonist_id": "c1",
                "health": 0.15,
                "priority": "CRITICAL",
            },
            {
                "type": "colonist_missing",
                "colonist_id": "c2",
                "colonist_name": "Jane",
                "priority": "HIGH",
            },
            {
                "type": "job_changed",
                "colonist_id": "c3",
                "old_job": "Wander",
                "new_job": "AttackMelee",
                "health": 0.3,
                "priority": "LOW",
            },
        ]

        # Run 100 iterations
        for _ in range(100):
            for event in test_events:
                start = time.time()
                actions = policy.decide(event)
                end = time.time()

                latency_ms = (end - start) * 1000
                latencies.append(latency_ms)

        # Calculate statistics
        avg_latency = np.mean(latencies)
        p50_latency = np.percentile(latencies, 50)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        max_latency = np.max(latencies)

        logger.info("Reflex latency (ms):")
        logger.info(f"  Average: {avg_latency:.3f}")
        logger.info(f"  P50: {p50_latency:.3f}")
        logger.info(f"  P95: {p95_latency:.3f}")
        logger.info(f"  P99: {p99_latency:.3f}")
        logger.info(f"  Max: {max_latency:.3f}")

        # Verify target met
        self.assertLess(p95_latency, 10.0, f"Reflex too slow: P95={p95_latency:.3f}ms")

    def test_observation_extraction_performance(self):
        """
        Benchmark: Observation extraction from state.

        Target: <5ms per extraction
        """
        from gym_env.spaces import ObservationSpace

        # Create test state
        test_state = {
            "frame_id": 1000,
            "global_state": {"colonist_count": 10, "wealth": 5000},
            "colonists": [
                {
                    "id": f"c{i}",
                    "health": 0.8 + i * 0.02,
                    "mood": 0.6,
                    "position": {"x": float(i * 10), "y": float(i * 5), "z": 0.0},
                    "current_job": "Haul",
                    "skills": [{"level": 10 + i}, {"level": 8}],
                    "needs": [{"value": 0.6}],
                    "health_capacities": [{"efficiency": 0.95}],
                    "drafted": False,
                }
                for i in range(10)
            ],
        }

        latencies: List[float] = []

        # Run 1000 extractions
        for _ in range(1000):
            start = time.time()
            obs = ObservationSpace.extract_observation(test_state)
            end = time.time()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

        # Calculate statistics
        avg_latency = np.mean(latencies)
        p50_latency = np.percentile(latencies, 50)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)

        logger.info("Observation extraction (ms):")
        logger.info(f"  Average: {avg_latency:.3f}")
        logger.info(f"  P50: {p50_latency:.3f}")
        logger.info(f"  P95: {p95_latency:.3f}")
        logger.info(f"  P99: {p99_latency:.3f}")

        # Verify target met
        self.assertLess(
            p95_latency, 5.0, f"Extraction too slow: P95={p95_latency:.3f}ms"
        )

    def test_reward_calculation_performance(self):
        """
        Benchmark: Reward calculation.

        Target: <1ms per calculation
        """
        from gym_env.rewards import RewardCalculator

        calculator = RewardCalculator()

        # Create test states
        test_state = {
            "colonists": [
                {"id": f"c{i}", "health": 0.8, "mood": 0.6} for i in range(10)
            ]
        }

        latencies: List[float] = []

        # Initialize with first state
        calculator.compute_reward(test_state)

        # Run 1000 calculations
        for i in range(1000):
            # Vary state slightly
            varied_state = {
                "colonists": [
                    {"id": f"c{j}", "health": 0.8 - i * 0.0001, "mood": 0.6}
                    for j in range(10)
                ]
            }

            start = time.time()
            reward = calculator.compute_reward(varied_state)
            end = time.time()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

        # Calculate statistics
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)

        logger.info("Reward calculation (ms):")
        logger.info(f"  Average: {avg_latency:.3f}")
        logger.info(f"  P95: {p95_latency:.3f}")

        # Verify target met
        self.assertLess(
            p95_latency, 1.0, f"Reward calc too slow: P95={p95_latency:.3f}ms"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    unittest.main()
