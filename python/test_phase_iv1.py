"""
Quick test runner for Phase IV.1 components.

Usage:
    uv run python python/test_phase_iv1.py
"""

import logging
import sys

# Add python dir to path
sys.path.insert(0, "python")

from client import (
    ActionQueue,
    ClientConfig,
    ClientState,
    ConnectionManager,
    EventQueue,
    MetricsCollector,
    PerformanceMetrics,
    SpectatorClient,
    StateQueue,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all imports work."""
    logger.info("✓ All imports successful")
    return True


def test_queue_creation():
    """Test queue instantiation."""
    state_q = StateQueue(maxsize=10)
    event_q = EventQueue(maxsize=100)
    action_q = ActionQueue(maxsize=100)

    assert state_q.empty()
    assert event_q.empty()
    assert action_q.empty()

    logger.info("✓ Queue creation successful")
    return True


def test_queue_operations():
    """Test basic queue operations."""
    state_q = StateQueue(maxsize=3)

    # Test put/get
    state_q.put({"frame": 1})
    state_q.put({"frame": 2})

    state = state_q.get()
    assert state["frame"] == 1

    # Test overflow
    state_q.put({"frame": 3})
    state_q.put({"frame": 4})
    state_q.put({"frame": 5})  # Should drop frame 2

    assert state_q.dropped_count == 1

    logger.info("✓ Queue operations successful")
    return True


def test_connection_manager():
    """Test ConnectionManager instantiation."""
    conn = ConnectionManager(host="localhost", port=50051, reconnect_attempts=5)

    assert conn.host == "localhost"
    assert conn.port == 50051
    assert not conn.is_connected()

    logger.info("✓ ConnectionManager creation successful")
    return True


def test_metrics_collector():
    """Test MetricsCollector."""
    metrics = MetricsCollector(window_size_seconds=5.0)

    # Record some events
    metrics.record_state_received()
    metrics.record_action_sent()
    metrics.record_latency("observation", 45.2)

    # Get metrics snapshot
    snapshot = metrics.get_metrics()

    assert isinstance(snapshot, PerformanceMetrics)
    assert snapshot.uptime_seconds >= 0

    logger.info("✓ MetricsCollector successful")
    return True


def test_client_config():
    """Test ClientConfig."""
    config = ClientConfig(
        host="localhost", port=50051, training_mode=True, inference_mode=False
    )

    assert config.host == "localhost"
    assert config.training_mode is True

    logger.info("✓ ClientConfig successful")
    return True


def test_spectator_client_creation():
    """Test SpectatorClient instantiation."""
    config = ClientConfig()
    client = SpectatorClient(config)

    assert client.config == config
    assert client._state == ClientState.INITIALIZED
    assert isinstance(client.connection, ConnectionManager)
    assert isinstance(client.state_queue, StateQueue)

    logger.info("✓ SpectatorClient creation successful")
    return True


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Phase IV.1 Core Infrastructure Tests")
    logger.info("=" * 60)

    tests = [
        test_imports,
        test_queue_creation,
        test_queue_operations,
        test_connection_manager,
        test_metrics_collector,
        test_client_config,
        test_spectator_client_creation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            logger.info(f"\nRunning: {test.__name__}")
            if test():
                passed += 1
        except Exception as e:
            logger.error(f"✗ {test.__name__} failed: {e}")
            failed += 1

    logger.info("\n" + "=" * 60)
    logger.info(f"Results: {passed} passed, {failed} failed")
    logger.info("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
