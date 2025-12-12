import sys
from pathlib import Path

import pytest

# Add the monorepo src directory to the Python path for shared module access
# This resolves to: /path/to/src (the parent of RimGym/)
# Required to import the 'shared' package which contains protobuf definitions
_monorepo_src = str(Path(__file__).parent.parent)
if _monorepo_src not in sys.path:
    sys.path.insert(0, _monorepo_src)


@pytest.fixture(scope="session")
def sample_fixture():
    return "sample data"


@pytest.fixture
def mock_client_config():
    """
    Fixture providing a mock ClientConfig for testing.
    
    Uses the correct parameter names from the ClientConfig dataclass
    in spectator_client.py (lines 36-80):
    - reconnect_attempts (not max_reconnect_attempts)
    - reconnect_backoff (with default value)
    - No auto_reconnect parameter (that's in ConnectionManager only)
    
    Returns:
        ClientConfig: A test configuration with sensible defaults
    """
    from client.spectator_client import ClientConfig
    
    return ClientConfig(
        host="localhost",
        port=50051,
        connect_timeout=5.0,
        reconnect_attempts=3,
        reconnect_backoff=0.5,
        training_mode=False,
        inference_mode=True,
        poll_interval_ms=100,
        max_state_queue_size=10,
        health_check_interval_ms=5000,
        max_inference_latency_ms=100,
        executive_policy=None,
        max_reflex_latency_ms=10,
        max_event_queue_size=100,
        reflex_policy=None,
        log_level="INFO",
        metrics_enabled=True,
        metrics_interval_ms=1000,
    )
