import os
import sys

import pytest

# Add the monorepo src directory to the Python path for shared module access
_monorepo_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _monorepo_src not in sys.path:
    sys.path.insert(0, _monorepo_src)


@pytest.fixture(scope="session")
def sample_fixture():
    return "sample data"
