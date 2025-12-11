# Self-Hosted Runner Setup for Integration Tests

## Overview

Integration tests require a Windows machine with RimWorld installed. GitHub hosted runners don't have RimWorld, so we use self-hosted runners for full integration testing.

## Prerequisites

- Windows 10/11 machine (always-on recommended)
- RimWorld 1.6 installed via Steam or standalone
- Sufficient disk space (~10 GB)
- Stable internet connection

## Setup Steps

### 1. Install RimWorld

```powershell
# Via Steam (recommended)
# Install via Steam client to: C:\Program Files (x86)\Steam\steamapps\common\RimWorld

# Or standalone
# Download from RimWorld website and install
```

### 2. Set Environment Variable

```powershell
# Set permanently
[System.Environment]::SetEnvironmentVariable('RIMWORLD_PATH', 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld', 'Machine')

# Verify
$env:RIMWORLD_PATH
```

### 3. Install Dependencies

```powershell
# .NET SDK 8.0
winget install Microsoft.DotNet.SDK.8

# UV for Python
pip install uv

# Git (if not already installed)
winget install Git.Git
```

### 4. Register Self-Hosted Runner

Go to your repository on GitHub:

1. Navigate to **Settings** → **Actions** → **Runners**
2. Click **New self-hosted runner**
3. Select **Windows**
4. Follow the provided commands:

```powershell
# Download
mkdir actions-runner; cd actions-runner
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-win-x64-2.311.0.zip -OutFile actions-runner-win-x64-2.311.0.zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("$PWD/actions-runner-win-x64-2.311.0.zip", "$PWD")

# Configure
./config.cmd --url https://github.com/YOUR_ORG/RimworldMLBridge --token YOUR_TOKEN

# Run as service (recommended)
./svc.sh install
./svc.sh start
```

### 5. Configure Runner

```powershell
# During configuration, set:
# - Runner name: rimworld-test-runner
# - Runner group: Default
# - Labels: self-hosted,Windows,X64
# - Work folder: _work (default)
```

### 6. Test Runner

Create a test workflow to verify:

```yaml
name: Test Self-Hosted Runner
on: workflow_dispatch

jobs:
  test:
    runs-on: self-hosted
    steps:
      - name: Check RimWorld
        run: |
          if (Test-Path $env:RIMWORLD_PATH) {
            Write-Host "✅ RimWorld found at $env:RIMWORLD_PATH"
          } else {
            Write-Error "❌ RimWorld not found"
            exit 1
          }
```

## Security Considerations

### Network Access

- Runner needs outbound access to GitHub (443/80)
- Runner needs outbound access to package managers (NuGet, PyPI)
- No inbound access required

### Firewall Rules

```powershell
# Allow RimWorld on local network (for TCP server)
New-NetFirewallRule -DisplayName "RimWorld ML Bridge" -Direction Inbound -Protocol TCP -LocalPort 50051 -Action Allow

# Verify
Get-NetFirewallRule -DisplayName "RimWorld ML Bridge"
```

### Isolation

- Runner runs in isolated directory
- Each job gets clean workspace
- Temporary files cleaned between runs

### Credentials

- Never store credentials in workflows
- Use GitHub Secrets for sensitive data
- RimWorld path is environment variable only

## Maintenance

### Update Runner

```powershell
cd C:\actions-runner
./svc.sh stop
./svc.sh uninstall

# Download new version and extract

./config.cmd remove --token YOUR_TOKEN
./config.cmd --url https://github.com/YOUR_ORG/RimworldMLBridge --token NEW_TOKEN
./svc.sh install
./svc.sh start
```

### Monitor Runner

```powershell
# Check service status
Get-Service actions.runner.*

# View logs
Get-Content C:\actions-runner\_diag\Runner_*.log -Tail 50

# Restart if needed
Restart-Service actions.runner.*
```

### Clean Workspace

```powershell
# Automatic cleanup happens between runs
# Manual cleanup if needed:
Remove-Item C:\actions-runner\_work\* -Recurse -Force
```

## Troubleshooting

### Runner Offline

```powershell
# Check service
Get-Service actions.runner.*

# Restart
Restart-Service actions.runner.*

# Check logs
Get-Content C:\actions-runner\_diag\Runner_*.log -Tail 100
```

### RimWorld Not Found

```powershell
# Verify path
Test-Path $env:RIMWORLD_PATH

# Check environment variable scope
[System.Environment]::GetEnvironmentVariable('RIMWORLD_PATH', 'Machine')

# Restart runner service after changing environment variables
Restart-Service actions.runner.*
```

### Tests Timing Out

- Increase timeout in workflow: `timeout-minutes: 15`
- Check RimWorld performance (close other programs)
- Verify no mods causing conflicts

### Port Already in Use

```powershell
# Check what's using port 50051
Get-NetTCPConnection -LocalPort 50051

# Kill process if needed
Stop-Process -Id <PID>
```

## Cost Optimization

### On-Demand Runner

For cost savings, use manual workflow dispatch:

```yaml
on:
  workflow_dispatch:  # Only run when manually triggered
```

Trigger only when:

- Merging to main
- Release candidate builds
- Major feature completion

### Scheduled Tests

```yaml
on:
  schedule:
    - cron: '0 2 * * 1-5'  # 2 AM weekdays
```

### Conditional Tests

```yaml
if: contains(github.event.head_commit.message, '[test-integration]')
```

Only run when commit message includes `[test-integration]`.

## Alternative: Cloud Gaming VM

For better isolation, use cloud gaming VM:

1. **Paperspace** (GPU-optimized Windows VM)
2. **Shadow** (cloud gaming service)
3. **Azure NVv3** (Windows VM with GPU)

Install RimWorld and runner on cloud VM, pay per hour only when running tests.

## Performance Benchmarks

Typical CI run times:

- C# Build: 1-2 minutes
- Python Tests: 30 seconds
- RimWorld Launch: 20-30 seconds
- Integration Tests: 30-60 seconds
- Total: ~4-5 minutes per run

Plan runner capacity accordingly (1 concurrent job typical).
