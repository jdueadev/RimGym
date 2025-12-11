# Docker Quick Reference Card

## 🚀 Quick Commands

### Start Testing

```bash
# Run full test suite (exits when done)
docker-compose up test

# Run integration server (stays running)
docker-compose up integration -d

# Stop integration server
docker-compose down
```

### View Logs

```bash
# Live logs
docker logs -f rimworldmlbridge-integration-1

# Last 50 lines
docker logs rimworldmlbridge-integration-1 --tail 50

# Search for errors
docker logs rimworldmlbridge-integration-1 2>&1 | grep -i error
```

### Check Status

```bash
# Container status
docker ps -a

# Resource usage
docker stats rimworldmlbridge-integration-1 --no-stream

# Health check status
docker inspect rimworldmlbridge-integration-1 | grep -A 10 Health
```

## ⚠️ Common Issues

### Container Won't Start

**Check line endings:**

```bash
file docker/entrypoint.sh
# Should show: "ASCII text" (not "with CRLF")
```

**Fix line endings:**

```powershell
# PowerShell
(Get-Content docker\entrypoint.sh -Raw) -replace "`r`n", "`n" | 
  Set-Content docker\entrypoint.sh -NoNewline
```

### Connection Refused (Port 50051)

**Wait for startup:**

```bash
# Wait 60 seconds, then check logs
docker logs rimworldmlbridge-integration-1 | grep "TCP+Protobuf server started"
```

**Verify port mapping:**

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
# Should show: 0.0.0.0:50051->50051/tcp
```

### Tests Fail

**Check test results:**

```bash
cat test_results.txt
```

**Run single test:**

```bash
docker-compose run test uv run pytest python/test_tcp_connection.py -v
```

### High CPU Usage

**Check for software rendering:**

```bash
docker-compose config | grep LIBGL
# Should NOT show LIBGL_ALWAYS_SOFTWARE
```

**Verify Xvfb only:**

```bash
docker exec rimworldmlbridge-integration-1 ps aux | grep Xvfb
# Should show: Xvfb :99 -screen 0 1024x768x24
```

## 🔧 Debugging

### Access Container Shell

```bash
docker exec -it rimworldmlbridge-integration-1 bash
```

### Check Mod Installation

```bash
docker exec rimworldmlbridge-integration-1 ls -la /opt/rimworld/Mods/
# Should show: Harmony/ and RimworldMLBridge/
```

### View ModsConfig.xml

```bash
docker exec rimworldmlbridge-integration-1 cat \
  /root/.config/unity3d/Ludeon\ Studios/RimWorld\ by\ Ludeon\ Studios/Config/ModsConfig.xml
```

### Test TCP Port Internally

```bash
docker exec rimworldmlbridge-integration-1 nc -zv localhost 50051
# Should show: Connection to localhost 50051 port [tcp/*] succeeded!
```

## 🔄 Clean Rebuild

### Complete Reset

```bash
# Stop and remove everything
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up integration
```

### Remove Images

```bash
# List RimWorld images
docker images | grep rimworld

# Remove specific image
docker rmi rimworldmlbridge-integration

# Remove all unused images
docker image prune -a
```

## 📊 Test from Python

### Quick Connection Test

```bash
uv run python python/test_tcp_connection.py
```

### Full Test Suite

```bash
uv run pytest python/test_automated_suite.py -v
```

### Hybrid Valve Tests

```bash
uv run python python/test_hybrid_valve.py
```

## 📝 Configuration Checklist

Before running, verify:

- [ ] `entrypoint.sh` has LF line endings
- [ ] Docker has 8GB+ RAM available
- [ ] Port 50051 is not in use
- [ ] RimWorld volume is set up correctly
- [ ] docker-compose.yml uses selective mounts (not `.:/app`)

## 🔗 Documentation Links

- **Setup**: [docker/QUICKSTART.md](QUICKSTART.md) (60 seconds)
- **Issues**: [docker/TROUBLESHOOTING.md](TROUBLESHOOTING.md) (comprehensive)
- **Details**: [docs/implementation/PHASE_IV_7_DOCKER_INTEGRATION.md](../docs/implementation/PHASE_IV_7_DOCKER_INTEGRATION.md)
- **Lessons**: [docs/implementation/DOCKER_LESSONS_LEARNED.md](../docs/implementation/DOCKER_LESSONS_LEARNED.md)

## 💡 Tips

### Performance

- Use Docker BuildKit: `export DOCKER_BUILDKIT=1`
- Enable WSL 2 backend (Windows)
- Allocate 4GB+ memory to Docker Desktop

### Development

- Mount only specific directories, not entire project
- Use `.dockerignore` to exclude `.venv`, `obj/`, `bin/`
- Test in Linux container early and often

### Troubleshooting

- Check logs first: `docker logs <container>`
- Verify file permissions: `docker exec <container> ls -la`
- Test networking: `docker exec <container> nc -zv host.docker.internal 50051`

## 🆘 Still Stuck?

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review container logs: `docker logs rimworldmlbridge-integration-1 > debug.log`
3. Verify RimWorld volume: `docker volume inspect rimworld-data`
4. Test without Docker (local RimWorld instance)
5. Ask for help with debug.log attached

---

**Print this card** for quick reference during development!
