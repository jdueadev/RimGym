# Docker Troubleshooting Guide

## Common Issues & Solutions

### Container Exits with Code 137

**Symptoms:**

- Container stops immediately after starting
- `docker logs` shows "Resolution too small (0x0)"
- TextureAtlas NullReferenceException

**Root Cause:**
RimWorld 1.6's Unity build requires graphics context even in batch mode. The `-nographics` flag alone fails because texture atlas initialization happens before mod loading.

**Solution:**
Use the `-quicktest` flag which enables developer mode and bypasses problematic UI initialization:

```bash
# Working configuration in docker-compose.yml
command: ["test"]  # Uses entrypoint.sh with -quicktest flag
```

The `entrypoint.sh` script automatically adds: `-batchmode -nographics -quicktest`

---

### "entrypoint.sh: not found" Error

**Symptoms:**

- Container fails with "exec: entrypoint.sh: not found" or "no such file or directory"
- Works in some environments but not others

**Root Cause:**
Windows text editors (including VS Code on Windows) save files with CRLF (carriage return + line feed) line endings. Linux expects LF (line feed) only. The bash interpreter fails to parse the shebang line correctly.

**Solution:**
Convert `entrypoint.sh` to Unix (LF) line endings:

**In VS Code:**

1. Click "CRLF" or "LF" in bottom-right status bar
2. Select "LF" from dropdown
3. Save file

**In PowerShell:**

```powershell
(Get-Content docker\entrypoint.sh -Raw) -replace "`r`n", "`n" | Set-Content docker\entrypoint.sh -NoNewline
```

**In Git Bash:**

```bash
dos2unix docker/entrypoint.sh
```

**Verify:**

```powershell
# Should show "UnixText"
Get-Content docker\entrypoint.sh -Raw | Format-Hex | Select-String "0D 0A"
# No output = LF only = correct
```

---

### Container Restart Loops / I/O Errors

**Symptoms:**

- Container repeatedly restarts
- Logs show "Input/output error" when accessing .venv or Python files
- Performance degradation on host system

**Root Cause:**
Mounting the entire project directory (`.:/app`) causes conflicts:

- Host's `.venv` (Windows) conflicts with container's `.venv` (Linux)
- File permission mismatches
- File locking issues between host and container

**Solution:**
Mount only specific directories needed by the container:

```yaml
volumes:
  - ./python:/app/python          # Python test scripts
  - ./Protos:/app/Protos          # Protobuf definitions
  - rimworld-data:/opt/rimworld   # Game data (separate volume)
   # DO NOT mount: .:/app or ./src/RimGym:/app
```

---

### Mods Not Loading

**Symptoms:**

- RimWorld starts but MLBridge mod not active
- No TCP server on port 50051
- Log shows "Active mods: Core, Royalty, Ideology..." but missing "RimTCP"

**Root Cause:**
RimWorld only loads mods listed in `ModsConfig.xml`. Having mod folders in `Mods/` is not sufficient.

**Solution:**
The `entrypoint.sh` script creates the correct `ModsConfig.xml` automatically. Verify it's being used:

```bash
# Check container logs for mod setup
docker logs rimgym-integration-1 | grep "Setting up ModsConfig.xml"

# Manually verify (if needed)
docker exec rimgym-integration-1 cat /root/.config/unity3d/Ludeon\ Studios/RimWorld\ by\ Ludeon\ Studios/Config/ModsConfig.xml
```

Required mods in config:

```xml
<activeMods>
  <li>ludeon.rimworld</li>
  <li>ludeon.rimworld.royalty</li>
  <li>ludeon.rimworld.ideology</li>
  <li>ludeon.rimworld.biotech</li>
  <li>ludeon.rimworld.anomaly</li>
  <li>brrainz.harmony</li>
   <li>unknwnentity.rimtcp</li>
</activeMods>
```

---

### High CPU Usage (2000%+)

**Symptoms:**

- System becomes unresponsive
- Container uses 20+ CPU cores at 100%
- `docker stats` shows CPU usage >2000%

**Root Cause:**
Attempted to use Mesa llvmpipe software rendering, which is CPU-intensive and unnecessary for RimWorld in headless mode.

**Solution:**
Do NOT use software rendering environment variables:

```yaml
# BAD - causes high CPU usage
environment:
  - LIBGL_ALWAYS_SOFTWARE=1
  - MESA_GL_VERSION_OVERRIDE=3.3
  - GALLIUM_DRIVER=llvmpipe

# GOOD - use standard Xvfb only
environment:
  - DISPLAY=:99
```

Standard Xvfb configuration is sufficient: `Xvfb :99 -screen 0 1024x768x24`

---

### Connection Refused on Port 50051

**Symptoms:**

- Python client gets `[Errno 111] Connection refused`
- `docker ps` shows port 50051 not mapped

**Root Cause:**
Port mapping may not be configured in docker-compose.yml or RimWorld hasn't started yet.

**Solution:**

1. Verify port mapping:

```yaml
ports:
  - "50051:50051"
```

1. Check RimWorld started and mod loaded:

```bash
# Look for these log lines:
docker logs rimgym-integration-1 | grep "TCP+Protobuf server started successfully"
docker logs rimgym-integration-1 | grep "Listening on 0.0.0.0:50051"
```

1. Wait for startup:

```bash
# Health check waits 60 seconds for game to start
docker-compose ps
# Should show: "healthy" status after startup period
```

---

### Tests Timeout / No Response

**Symptoms:**

- Test script hangs waiting for response
- No error messages, just timeout
- Logs show game is running

**Root Cause:**
RimWorld game may be paused or in wrong state. Training mode requires explicit STEP command.

**Solution:**
Verify game state in logs:

```bash
# Check for tick progression
docker logs rimgym-integration-1 | grep "DoSingleTick"

# Check for server responses
docker logs rimgym-integration-1 | grep "Sending state"
```

If training mode is stuck, send a STEP command:

```python
from mlbridge_pb2 import CommandMessage
msg = CommandMessage(step_ticks=60, training_mode=True)
# Send via TCP connection
```

---

## Configuration Validation Checklist

Before deploying, verify:

- [ ] `entrypoint.sh` has LF line endings (not CRLF)
- [ ] `docker-compose.yml` uses selective volume mounts (not `.:/app`)
- [ ] Command includes `-quicktest` flag (via entrypoint.sh)
- [ ] No software rendering environment variables set
- [ ] Port 50051 mapped correctly
- [ ] Health check configured with 60s start period
- [ ] Memory limits appropriate (4GB for RimWorld)
- [ ] ModsConfig.xml includes Harmony + RimTCP

---

## Debugging Commands

### View Container Logs

```bash
# Last 100 lines
docker logs rimgym-integration-1 --tail 100

# Follow logs in real-time
docker logs -f rimgym-integration-1

# Search logs for errors
docker logs rimgym-integration-1 2>&1 | grep -i "error\|exception\|fail"
```

### Check Container Status

```bash
# Container list with status
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Resource usage
docker stats rimgym-integration-1 --no-stream

# Health check status
docker inspect rimgym-integration-1 | jq '.[0].State.Health'
```

### Interactive Debugging

```bash
# Access container shell
docker exec -it rimgym-integration-1 bash

# Check files inside container
docker exec rimgym-integration-1 ls -la /opt/rimworld/Mods/

# Check ModsConfig.xml
docker exec rimgym-integration-1 cat /root/.config/unity3d/Ludeon\ Studios/RimWorld\ by\ Ludeon\ Studios/Config/ModsConfig.xml

# Test TCP port from inside container
docker exec rimgym-integration-1 nc -zv localhost 50051
```

### Clean Rebuild

```bash
# Remove everything and rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up integration
```

---

## Still Having Issues?

If none of these solutions work:

1. **Capture Full Logs:**

   ```bash
   docker logs rimgym-integration-1 > debug_logs.txt 2>&1
   ```

2. **Verify RimWorld Installation:**
   - Check `/opt/rimworld` volume contains game files
   - Verify `RimWorldLinux` executable is present and executable

3. **Check System Requirements:**
   - Docker Desktop 4.x+ on Windows
   - WSL 2 backend enabled
   - At least 8GB RAM available (4GB for container + 4GB for host)
   - Linux container mode (not Windows containers)

4. **Test Without Docker:**
   - Run `python/test_tcp_connection.py` against local RimWorld instance
   - Verify mod works outside Docker environment

5. **Review Recent Changes:**
   - Check if `entrypoint.sh` or `docker-compose.yml` were modified
   - Verify no uncommitted changes to critical files

6. **Consult Documentation:**
   - See `docker/README.md` for full setup instructions
   - See `docs/guides/installation.md` for RimWorld volume setup
   - See `memory-bank/progress.md` for Phase IV.7 implementation details
