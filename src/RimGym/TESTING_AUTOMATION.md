# Testing Automation Guide

## Overview

The automated test suite (`test_automated_suite.py`) provides full CI/CD-ready testing for the Hybrid Valve implementation. It can:

1. Launch RimWorld automatically in dev mode
2. Run comprehensive tests at multiple game speeds
3. Generate detailed test reports
4. Close RimWorld automatically after completion

## Quick Start

### Manual Testing (RimWorld already running)

```powershell
# Run tests against already-running RimWorld
uv run python\test_automated_suite.py --no-launch --no-close
```

### Fully Automated (Launch + Test + Close)

```powershell
# Set RimWorld path (one-time setup)
$env:RIMWORLD_PATH = "C:\Program Files (x86)\Steam\steamapps\common\RimWorld"

# Run full automated suite
uv run python\test_automated_suite.py
```

### Generate Report File

```powershell
uv run python\test_automated_suite.py --output test_results.txt
```

## Prerequisites

### 1. RimWorld Installation

- RimWorld 1.6 with ML Bridge mod installed
- Mod dependencies: Harmony

### 2. Python Environment

```powershell
# Install dependencies (auto-handled by uv)
uv sync
```

### 3. Environment Setup

**Option A: Environment Variable (Recommended)**

```powershell
# Windows PowerShell
[System.Environment]::SetEnvironmentVariable('RIMWORLD_PATH', 'C:\Path\To\RimWorld', 'User')

# Windows CMD
setx RIMWORLD_PATH "C:\Path\To\RimWorld"

# Linux/Mac
export RIMWORLD_PATH="/path/to/RimWorld"
```

**Option B: Command-Line Argument**

```powershell
uv run python\test_automated_suite.py --rimworld-path "C:\Path\To\RimWorld"
```

## Test Scenarios

The automated suite runs **4 comprehensive test scenarios**:

### 1. Paused State Test

- **Training Mode**: Verifies exact 60-tick control
- **Inference Mode**: Verifies 0 ticks advanced (game paused)
- **Expected**: Training passes, inference shows 0 movement

### 2. 1x Speed Test (Normal)

- **Training Mode**: 60 ticks in ~1000ms
- **Inference Mode**: 100-140 ticks in 2 seconds
- **Expected**: ~120 ticks/2s in inference mode

### 3. 2x Speed Test (Fast)

- **Training Mode**: 60 ticks in ~500ms
- **Inference Mode**: 250-400 ticks in 2 seconds
- **Expected**: ~300 ticks/2s in inference mode

### 4. 3x Speed Test (Superfast)

- **Training Mode**: 60 ticks in ~200ms
- **Inference Mode**: 600-800 ticks in 2 seconds
- **Expected**: ~720 ticks/2s in inference mode

## Command-Line Options

```
usage: test_automated_suite.py [OPTIONS]

Options:
  --rimworld-path PATH   Path to RimWorld installation
  --no-launch           Skip launching RimWorld (assume already running)
  --no-close            Keep RimWorld open after tests complete
  --output FILE         Save test report to file
  -h, --help            Show this help message
```

## Usage Examples

### Development Workflow

```powershell
# Keep RimWorld open between test runs for faster iteration
uv run python\test_automated_suite.py --no-launch --no-close
```

### CI/CD Pipeline

```powershell
# Full automated run with report generation
uv run python\test_automated_suite.py --output ci_results.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed!"
    exit 1
}
```

### Debugging Specific Speed

```powershell
# Launch RimWorld but keep it open for manual inspection
uv run python\test_automated_suite.py --no-close
```

## RimWorld QuickTest Mode

The automation uses RimWorld's `-quicktest` flag to load quickly:

- Skips main menu
- Loads directly into a game (uses last save or new random)
- Enables dev mode automatically
- Reduces startup time from ~60s to ~20s

**Note**: First run may be slow as RimWorld generates a new world. For fastest results, have a save file ready.

## Expected Output

### Successful Run

```
🚀 Launching RimWorld from: C:\...\RimWorld
   Process ID: 12345
🔄 Waiting for RimWorld to start (timeout: 90s)...
✅ Connected to RimWorld!

============================================================
AUTOMATED TEST SUITE - Phase III Hybrid Valve
============================================================

============================================================
TEST: Paused
============================================================
🎛️  Setting speed to: Paused
   Status: Speed changed to Paused
📍 Testing Training Mode...
   ✅ Training: 60 ticks in 1132ms
📍 Testing Inference Mode...
   ✅ Inference: 0 ticks in 2012ms

[... tests for 1x, 2x, 3x speeds ...]

============================================================
TEST REPORT
============================================================
Test Date: 2025-12-10 14:30:45
Total Tests: 4

✅ Passed: 4
❌ Failed: 0

============================================================

✅ PASS - Paused
  Training: 60 ticks in 1132ms
  Inference: 0 ticks in 2012ms

✅ PASS - 1x Speed
  Training: 60 ticks in 1048ms
  Inference: 120 ticks in 2013ms

[...]

🛑 Closing RimWorld...
   RimWorld closed
```

### Failed Test

```
❌ FAIL - 2x Speed
  Training: 60 ticks in 375ms
  Inference: 50 ticks in 2014ms
  Error: Inference mode: Expected 250-400 ticks, got 50
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup RimWorld
        run: |
          # Install RimWorld (use cached version or download)
          # Copy mod to RimWorld/Mods/
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install UV
        run: pip install uv
      
      - name: Run Automated Tests
        env:
          RIMWORLD_PATH: ${{ env.RIMWORLD_INSTALL_DIR }}
        run: |
          uv run python\test_automated_suite.py --output test_results.txt
      
      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test_results.txt
```

## Troubleshooting

### RimWorld Not Found

```
❌ Error: RimWorld path not specified
```

**Solution**: Set `RIMWORLD_PATH` environment variable or use `--rimworld-path`

### Connection Timeout

```
❌ Connection timeout after 90s
```

**Solutions**:

- Increase timeout in code (default 90s)
- Check if port 50051 is blocked by firewall
- Ensure mod is enabled in RimWorld
- Check RimWorld logs for mod errors

### Game Crashes During Tests

**Solutions**:

- Check RimWorld logs: `%USERPROFILE%\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Player.log`
- Disable other mods that might conflict
- Ensure you have a valid save file or world seed

### Tests Fail on Specific Speed

**Solutions**:

- Check if game is actually running at expected speed
- Look for performance bottlenecks (CPU, mods, map size)
- Adjust expected tick ranges in `run_speed_test()` configurations

## Performance Notes

- **Startup Time**: ~20-30s with `-quicktest`, ~60s without
- **Connection Timeout**: 90s default (configurable)
- **Test Duration**: ~30s for all 4 speed tests
- **Total Runtime**: ~1-2 minutes from launch to completion

## Extending the Tests

### Add New Speed Test

Edit `run_full_suite()`:

```python
speeds = [
    # ... existing speeds ...
  ("4x Speed", rimgym_pb2.SPEED_ULTRAFAST, 900, 1100),  # ~1000 ticks expected
]
```

### Add Custom Validation

Edit `run_speed_test()`:

```python
# Add after inference test
if speed_name == "1x Speed":
    # Custom validation for 1x speed
    if not (118 <= ticks_advanced <= 122):
        results['error'] = "1x speed out of tight tolerance"
```

### Add Velocity Tests

```python
# In run_speed_test(), after inference test:
before_pos = before.colonists[0].position
after_pos = after.colonists[0].position
velocity = calculate_velocity(before_pos, after_pos, elapsed_ms)
results['velocity'] = velocity
```

## Future Enhancements

- [ ] Parallel test execution (multiple RimWorld instances)
- [ ] Performance regression detection (compare against baseline)
- [ ] Integration with pytest for IDE support
- [ ] Automatic screenshot capture on failures
- [ ] Network latency simulation tests
- [ ] Memory leak detection over extended runs
