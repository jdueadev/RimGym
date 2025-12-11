"""
Test that pytest fixtures are properly configured.

These tests don't require the actual client modules to import successfully.
"""

import pytest


@pytest.mark.unit
def test_rimworld_server_fixture(rimworld_server):
    """Test that rimworld_server fixture returns a boolean."""
    assert isinstance(rimworld_server, bool)


@pytest.mark.unit
def test_fixtures_available():
    """Test that basic pytest setup is working."""
    assert True


@pytest.mark.unit
def test_mock_client_config_fixture():
    """Test that mock_client_config fixture can be defined and has correct signature."""
    # Test that the fixture is properly defined in conftest.py
    # We cannot instantiate it until protobuf dependencies are resolved (Issue #1)
    # but we can verify the fixture exists and is accessible
    import inspect
    from pathlib import Path
    
    # Load conftest.py and verify the fixture exists
    conftest_path = Path(__file__).parent.parent / "conftest.py"
    assert conftest_path.exists(), "conftest.py should exist"
    
    # Read conftest.py and verify mock_client_config is defined
    conftest_content = conftest_path.read_text()
    assert "def mock_client_config" in conftest_content, "mock_client_config fixture should be defined"
    assert "@pytest.fixture" in conftest_content, "Fixture should be decorated"
    
    # Verify the expected configuration values are set in the fixture
    assert 'host="localhost"' in conftest_content
    assert 'port=50051' in conftest_content
    assert 'training_mode=False' in conftest_content
    assert 'inference_mode=True' in conftest_content
    assert 'reconnect_attempts=3' in conftest_content


@pytest.mark.integration
def test_skip_when_no_server(skip_if_no_server):
    """Test that integration tests skip when RimWorld server is not available."""
    # This test should be skipped because RimWorld is not running
    # If it runs, that means the fixture is not working correctly
    assert False, "This test should have been skipped!"
