import sys
from pathlib import Path

import pytest

# Fix import paths
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="session")
def rimworld_server():
    """Check if RimWorld server is available."""
    import socket
    try:
        with socket.create_connection(("localhost", 50051), timeout=2):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def skip_if_no_server(rimworld_server):
    """Skip integration tests if RimWorld server not available."""
    if not rimworld_server:
        pytest.skip("RimWorld server not available")


@pytest.fixture
def mock_client_config():
    """Provide a standard test configuration."""
    from client import ClientConfig
    return ClientConfig(
        host="localhost",
        port=50051,
        training_mode=False,
        inference_mode=True,
        reconnect_attempts=3
    )
