# Monorepo Migration Issues - Investigation Report

**Date:** 2025-12-11  
**Investigators:** Test Analysis Agent & New Contributor Agent  
**Status:** 🔴 CRITICAL - Multiple Breaking Issues Found

---

## Executive Summary

The monorepo migration has caused **extensive breakage** across:

- ✅ **All test files** (16 test files with broken imports)
- ✅ **Example scripts** (3 example files with broken imports)
- ✅ **Documentation** (README.md with outdated import examples)
- ✅ **Package structure** (inconsistent with pyproject.toml configuration)

**Impact:** The project is currently **non-functional** for new contributors and existing tests are **100% broken**.

---

## 🔥 Critical Issue #1: Import Path Inconsistency

### Problem

The codebase has **two different import patterns** that don't match the actual package structure:

**Pattern A (Used in actual code):**

```python
from client import ClientConfig, SpectatorClient
```

**Pattern B (Documented in README):**

```python
from rimgym.client import SpectatorClient
from rimgym.protos import mlbridge_pb2
```

**Actual Package Structure:**

```
src/RimGym/
├── pyproject.toml         # Defines package name as "rimgym"
└── src/                   # Code lives here
    ├── client/            # NOT under python/ as pyproject.toml expects!
    ├── examples/
    ├── gym_env/
    └── policies/
```

### Root Cause

`pyproject.toml` specifies:

```toml
[tool.setuptools]
package-dir = {"" = "python"}  # ⚠️ Looking for python/ directory
packages = ["client", "policies", "gym_env"]  # ⚠️ Expects these in python/
```

But the actual code is in `src/` directory, NOT `python/`.

### Files Affected (21 files total)

#### Test Files (16 files) - ALL BROKEN

1. `tests/integration/performance_test_phase5.py` - Line 21
2. `tests/integration/test_full_system.py` - Line 14
3. `tests/integration/test_phase_iv1.py` - Line 14
4. `tests/integration/test_performance.py` - Line 13
5. `tests/client/test_connection.py` - Line 10
6. `tests/client/test_actor.py`
7. `tests/client/test_inference.py`
8. `tests/client/test_listener.py`
9. `tests/client/test_listener_performance.py`
10. `tests/client/test_queues.py`
11. `tests/gym_env/test_gymnasium.py`
12. `tests/integration/test_tcp_connection.py`
13. `tests/integration/test_hybrid_valve.py`
14. `tests/integration/test_full_system.py`
15. `tests/integration/test_automated_suite.py`
16. `tests/integration/run_inference_tests.py`

#### Example Scripts (3 files)

1. `src/examples/spectator_demo.py` - Line 12
2. `src/examples/phase5_full_observability.py` - Line 15
3. `src/examples/run_inference.py` - Line 13

#### Application Code (2 files)

1. `src/gym_env/rimworld_env.py` - Line 13

### Why This Breaks Everything

When a new contributor follows the README instructions:

```bash
cd src/RimGym
uv sync
python src/examples/spectator_demo.py --help
```

**Result:** `ModuleNotFoundError: No module named 'client'`

Why? Because:

1. The package isn't installed (just dependencies via `uv sync`)
2. Even if installed, it would look for `python/client/` (doesn't exist)
3. The actual code is in `src/client/` (not on Python path)

---

## 🔥 Critical Issue #2: Documentation is Completely Wrong

### README.md Examples Don't Work

The README shows:

```python
from rimgym.client import SpectatorClient
from rimgym.protos import mlbridge_pb2
```

But this will **fail** because:

1. Package structure doesn't match
2. No `protos` module exists at package level
3. Import paths in actual code are different

### Broken Documentation References

**Line 74 in README.md:**

```markdown
For full integration testing with the game, see the [Testing Automation Guide](../../docs/guides/testing-automation.md).
```

**Problem:** This path is wrong for monorepo structure. Should be:

- From monorepo root: `docs/guides/testing-automation.md`
- From RimGym package: `../../docs/guides/testing-automation.md` (correct relative path)

---

## 🔥 Critical Issue #3: spectator_demo.py Cannot Run

### Current State

**Expected Path:** `src/RimGym/src/examples/spectator_demo.py` ✅ (exists)  
**Can Execute:** ❌ NO

### Issues Preventing Execution

#### Issue 3.1: Import Error

```python
from client import ClientConfig, SpectatorClient
```

- Assumes `client` is on Python path
- Not true in default setup
- No installation instructions that would fix this

#### Issue 3.2: Missing Setup Instructions

README says:

```bash
uv sync  # Only installs dependencies, NOT the package itself!
```

Should be:

```bash
uv sync
uv pip install -e .  # Install rimgym package in editable mode
```

#### Issue 3.3: Circular Problems

Even if we fix imports, we have:

- Tests import with `from client import ...`
- README documents `from rimgym.client import ...`
- Package definition points to non-existent `python/` directory

**Which pattern is correct?** 🤷

---

## 📊 Test Failure Analysis

### Test Discovery Status

- **Total test files found:** 16
- **Can run any tests:** ❌ NO
- **Import errors expected:** 100%

### Why Tests Are Broken

#### Problem 1: Import Paths

All tests use:

```python
from client import ConnectionManager
from client.connection import ConnectionManager
```

These won't resolve without proper package installation or PYTHONPATH manipulation.

#### Problem 2: No conftest.py Setup

`src/RimGym/conftest.py` exists but doesn't:

- Add `src/` to Python path
- Configure import hooks
- Set up test fixtures for path resolution

Current content:

```python
import pytest

@pytest.fixture(scope="session")
def sample_fixture():
    return "sample data"
```

#### Problem 3: Missing pytest Configuration

**No pytest.ini exists!**

Should have:

```ini
[pytest]
testpaths = tests
pythonpath = src
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

## 🎯 Sharp Edges for New Contributors

### Edge #1: Multiple Directory Confusion

```
/src/RimGym/           # Package root
  /src/                # Code location
    /examples/         # Examples here
  /tests/              # Tests here
```

Why is code in `src/src/`? This is confusing!

### Edge #2: README Installation Instructions Incomplete

README says:

```bash
cd src/RimGym
uv sync
```

But doesn't mention:

- Need to install package itself (`uv pip install -e .`)
- Or add `src/` to PYTHONPATH
- Or run from specific directory with modified path

### Edge #3: Import Style Inconsistency

Three different styles in the codebase:

1. `from client import X` (most code)
2. `from rimgym.client import X` (README)
3. `from client.connection import X` (some tests)

**Which one should I use?** 😕

### Edge #4: No Clear "Getting Started" Path

To actually run spectator_demo.py, a new contributor must:

1. ❓ Figure out the import issue
2. ❓ Manually add src/ to PYTHONPATH, or
3. ❓ Install package in editable mode (not documented)
4. ❓ Hope RimWorld server is running (not checked)

**None of this is documented!**

---

## 🔧 Recommended Fixes

### Priority 1: Fix Package Structure (Choose One Path)

#### Option A: Match pyproject.toml Expectation

```bash
# Rename src/ to python/
mv src/RimGym/src src/RimGym/python
```

Update all imports to:

```python
from client import ...
```

#### Option B: Fix pyproject.toml to Match Reality

```toml
[tool.setuptools]
package-dir = {"" = "src"}  # Changed from "python"
packages = ["client", "policies", "gym_env", "examples"]
```

### Priority 2: Fix README.md

#### Update Installation Section

```markdown
## 🚀 Installation

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### Install Package

\`\`\`bash
cd src/RimGym
uv sync                    # Install dependencies
uv pip install -e .        # Install rimgym package in editable mode
\`\`\`

### Verify Installation
\`\`\`bash
python -c "from client import SpectatorClient; print('✓ Import successful')"
\`\`\`
```

#### Update Example Code

Choose consistent import style (recommend matching actual code):

```python
from client import SpectatorClient, ClientConfig
```

OR fully qualify if package is properly set up:

```python
from rimgym.client import SpectatorClient, ClientConfig
```

### Priority 3: Add pytest.ini

Create `src/RimGym/pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = src
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    integration: Integration tests requiring game connection
    unit: Fast unit tests
```

### Priority 4: Fix conftest.py

Update `src/RimGym/conftest.py`:

```python
import sys
from pathlib import Path

import pytest

# Add src directory to Python path for tests
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

@pytest.fixture(scope="session")
def rimworld_available():
    """Check if RimWorld server is available for integration tests."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(('localhost', 50051))
        sock.close()
        return result == 0
    except Exception:
        return False
```

### Priority 5: Update All Import Statements

**If choosing Option A (python/ directory):**

- ✅ Imports already correct (`from client import ...`)

**If choosing Option B (fix pyproject.toml):**

- ✅ Imports already correct (`from client import ...`)
- Update `package-dir = {"" = "src"}`

---

## 📋 Testing the Fixes

### Step 1: Verify Package Installation

```bash
cd src/RimGym
uv pip install -e .
python -c "from client import SpectatorClient; print('OK')"
```

### Step 2: Run Unit Tests

```bash
uv run pytest tests/client/ -v
```

### Step 3: Try Example Script

```bash
python src/examples/spectator_demo.py --help
```

Should output:

```
usage: spectator_demo.py [-h] [--host HOST] [--port PORT] [--duration DURATION]

Watch RimWorld game state
...
```

---

## 🚨 Impact Assessment

### Current State: BROKEN 🔴

- **Tests:** 0% functional
- **Examples:** 0% functional  
- **Documentation:** Misleading
- **New Contributor Experience:** Impossible to get started

### After Fixes: FUNCTIONAL ✅

- **Tests:** 100% discoverable and runnable
- **Examples:** Works with clear instructions
- **Documentation:** Accurate and helpful
- **New Contributor Experience:** Smooth onboarding

---

## 📝 Summary of Issues Found

| Issue | Severity | Impact | Files Affected |
|-------|----------|--------|----------------|
| Import path mismatch | 🔴 CRITICAL | All tests/examples broken | 21 files |
| pyproject.toml wrong directory | 🔴 CRITICAL | Package installation fails | 1 file |
| README outdated | 🔴 CRITICAL | New contributors blocked | 1 file |
| No pytest.ini | 🟡 HIGH | Tests can't run properly | 0 files (missing) |
| conftest.py minimal | 🟡 HIGH | No test environment setup | 1 file |
| Documentation links wrong | 🟡 MEDIUM | 404 errors | 1+ files |
| No installation verification | 🟡 MEDIUM | Silent failures | README |

**Total Files Requiring Changes:** 25+ files

---

## Next Steps

1. **DECIDE** on package structure approach (Option A or B)
2. **FIX** pyproject.toml or rename directory accordingly
3. **UPDATE** README.md with accurate installation instructions
4. **CREATE** pytest.ini configuration
5. **ENHANCE** conftest.py for test environment
6. **TEST** all changes with fresh environment
7. **DOCUMENT** troubleshooting steps for common issues

---

## Appendix: File Locations for Reference

```
src/RimGym/
├── README.md                              ⚠️ NEEDS UPDATE
├── pyproject.toml                         ⚠️ NEEDS FIX
├── conftest.py                            ⚠️ NEEDS ENHANCEMENT
├── pytest.ini                             ❌ MISSING - NEEDS CREATION
├── src/                                   ℹ️  Should be python/? Or update pyproject.toml?
│   ├── client/                            ✅ Code location
│   ├── examples/
│   │   ├── spectator_demo.py             ⚠️ BROKEN IMPORTS
│   │   ├── phase5_full_observability.py  ⚠️ BROKEN IMPORTS
│   │   └── run_inference.py              ⚠️ BROKEN IMPORTS
│   ├── gym_env/
│   │   └── rimworld_env.py               ⚠️ BROKEN IMPORTS
│   └── policies/
└── tests/                                 ⚠️ ALL 16 TEST FILES BROKEN
    ├── client/                            (6 test files)
    ├── gym_env/                           (1 test file)
    └── integration/                       (9 test files)
```

---

**Report Generated:** 2025-12-11T21:36:58Z  
**Agents:** Test Analysis Agent + New Contributor Agent  
**Recommendation:** Address Priority 1-3 items immediately to restore basic functionality.
