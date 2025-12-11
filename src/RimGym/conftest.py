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
