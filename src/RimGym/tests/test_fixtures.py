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


@pytest.mark.integration
def test_skip_when_no_server(skip_if_no_server):
    """Test that integration tests skip when RimWorld server is not available."""
    # This test should be skipped because RimWorld is not running
    # If it runs, that means the fixture is not working correctly
    assert False, "This test should have been skipped!"
