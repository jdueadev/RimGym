"""
Tests for pytest fixtures defined in conftest.py.

These tests validate that fixtures are properly configured and return
expected values for use in other tests.
"""

import pytest

from client.spectator_client import ClientConfig


@pytest.mark.unit
def test_mock_client_config_fixture_exists(mock_client_config):
    """Test that mock_client_config fixture is available and returns ClientConfig."""
    assert mock_client_config is not None
    assert isinstance(mock_client_config, ClientConfig)


@pytest.mark.unit
def test_mock_client_config_correct_parameters(mock_client_config):
    """Test that mock_client_config uses correct ClientConfig parameter names."""
    # Connection parameters - these are the CORRECT parameter names
    assert hasattr(mock_client_config, "host")
    assert hasattr(mock_client_config, "port")
    assert hasattr(mock_client_config, "connect_timeout")
    assert hasattr(mock_client_config, "reconnect_attempts")  # NOT max_reconnect_attempts
    assert hasattr(mock_client_config, "reconnect_backoff")
    
    # Operating mode parameters
    assert hasattr(mock_client_config, "training_mode")
    assert hasattr(mock_client_config, "inference_mode")
    
    # Verify the fixture does NOT have incorrect parameters
    # These belong to ConnectionManager, not ClientConfig
    assert not hasattr(mock_client_config, "auto_reconnect")
    assert not hasattr(mock_client_config, "max_reconnect_attempts")


@pytest.mark.unit
def test_mock_client_config_values(mock_client_config):
    """Test that mock_client_config has sensible default values."""
    assert mock_client_config.host == "localhost"
    assert mock_client_config.port == 50051
    assert mock_client_config.connect_timeout == 5.0
    assert mock_client_config.reconnect_attempts == 3
    assert mock_client_config.reconnect_backoff == 0.5
    assert mock_client_config.training_mode is False
    assert mock_client_config.inference_mode is True


@pytest.mark.unit
def test_mock_client_config_can_be_instantiated_correctly():
    """Test that ClientConfig can be instantiated with correct parameters."""
    # This should work without errors
    config = ClientConfig(
        host="testhost",
        port=12345,
        connect_timeout=10.0,
        reconnect_attempts=5,
        reconnect_backoff=1.0,
        training_mode=True,
        inference_mode=False,
    )
    
    assert config.host == "testhost"
    assert config.port == 12345
    assert config.reconnect_attempts == 5
    assert config.reconnect_backoff == 1.0


@pytest.mark.unit
def test_mock_client_config_validates_modes(mock_client_config):
    """Test that ClientConfig validates training/inference mode settings."""
    # The __post_init__ should ensure at least one mode is enabled
    # mock_client_config should have inference_mode=True by default
    assert mock_client_config.inference_mode is True or mock_client_config.training_mode is True
