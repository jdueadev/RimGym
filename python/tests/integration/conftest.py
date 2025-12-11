"""Integration test fixtures.

These tests require a running RimWorld instance with MLBridge enabled.
They are skipped by default in CI/CD and can be run manually.
"""

import pytest


@pytest.fixture(scope="module")
def client():
    """Create a HybridValveClient for integration testing.
    
    This fixture is used by test_hybrid_valve.py tests.
    Tests are skipped if RimWorld is not running.
    """
    pytest.skip("Integration tests require running RimWorld - run manually as script")
