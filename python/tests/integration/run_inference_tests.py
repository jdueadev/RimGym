#!/usr/bin/env python
"""
Direct test runner for inference tests to bypass timeout issues with pytest invocation.
"""

import sys
import unittest

# Add parent directory to path
sys.path.insert(0, ".")

# Import test module
from tests.client import test_inference

if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromModule(test_inference))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
