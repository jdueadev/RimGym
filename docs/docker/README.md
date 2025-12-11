# Docker-based Testing for RimWorld ML Bridge

## Overview

Run **fully automated tests** in Docker containers instead of self-hosted runners or cloud VMs. This provides:

- ✅ **Reproducible** environment
- ✅ **Portable** across machines
- ✅ **CI/CD ready** (runs on GitHub Actions)
- ✅ **No manual setup** after initial configuration
- ✅ **Cost-effective** (no VM charges)

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup guide (60 seconds)
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions ⚠️
- **[README.md](README.md)** - This file (comprehensive reference)

## Quick Start

### Prerequisites

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
2. **RimWorld Linux version** (from Steam or standalone)

### Setup RimWorld Volume

**Option 1: Mount Steam Library (Recommended)**

```bash
# Linux/Mac
docker volume create rimworld-data
docker run --rm -v /path/to/Steam/steamapps/common/RimWorld:/source -v rimworld-data:/dest alpine cp -r /source/. /dest/

# Windows (PowerShell)
docker volume create rimworld-data
docker run --rm -v "C:\Program Files (x86)\Steam\steamapps\common\RimWorld:/source" -v rimworld-data:/dest alpine cp -r /source/. /dest/
```

**Option 2: Copy from Local Installation**

```bash
# Copy RimWorld to Docker volume
docker run --rm -v rimworld-data:/opt/rimworld -v ./rimworld-files:/source alpine cp -r /source/. /opt/rimworld/
```

**Option 3: Build Custom Image**

See [Custom Image Build](#custom-image-build) section.

### Run Tests

```bash
# Build and run tests (automated suite, exits when complete)
docker-compose up test

# Run integration server (stays running for manual testing)
docker-compose up integration -d

# Check logs
docker logs rimworldmlbridge-integration-1

# Test connection from Python
uv run python python/test_tcp_connection.py

# Or with Docker directly
docker build -t rimworld-ml-bridge .
docker run --rm \
  -v rimworld-data:/opt/rimworld \
  -v $(pwd)/test_results.txt:/app/test_results.txt \
  rimworld-ml-bridge test
```

### View Results

```bash
# Test results are written to test_results.txt
cat test_results.txt
```

## Architecture

### Multi-Stage Build

```
Stage 1: Base (Ubuntu + .NET + Python)
   ↓
Stage 2: RimWorld Base (Headless X server)
   ↓
Stage 3: Builder (Build C# + Python)
   ↓
Stage 4: Test Runner (Runtime environment)
```

### Headless Mode

RimWorld runs in headless mode:

- `-batchmode`: No Unity editor
- `-nographics`: No rendering
- `-quicktest`: Fast startup with dev mode
- Xvfb: Virtual X server (Unity still needs X11)

## GitHub Actions Integration

### Using Docker in CI

Replace self-hosted runner with Docker-based tests:

```yaml
name: Docker Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Restore RimWorld Cache
        uses: actions/cache@v4
        with:
          path: rimworld-cache
          key: rimworld-linux-${{ hashFiles('**/About.xml') }}
      
      - name: Build Docker image
        run: docker build -t rimworld-ml-bridge .
      
      - name: Create RimWorld volume
        run: |
          docker volume create rimworld-data
          # Mount cached RimWorld if available
          if [ -d rimworld-cache ]; then
            docker run --rm -v $(pwd)/rimworld-cache:/source -v rimworld-data:/dest alpine cp -r /source/. /dest/
          fi
      
      - name: Run tests
        run: |
          docker run --rm \
            -v rimworld-data:/opt/rimworld \
            -v $(pwd)/test_results.txt:/app/test_results.txt \
            rimworld-ml-bridge test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test_results.txt
      
      - name: Check results
        run: |
          if grep -q "❌ Failed: [1-9]" test_results.txt; then
            echo "Tests failed!"
            exit 1
          fi
```

## Custom Image Build

### With RimWorld Included (Private Registry)

**⚠️ Warning**: Only use for private registries. Don't publish images with RimWorld to public registries (licensing).

```dockerfile
# Dockerfile.with-rimworld
FROM rimworld-ml-bridge:base

# Copy RimWorld from build context
COPY rimworld-linux/ ${RIMWORLD_PATH}/
RUN chmod +x ${RIMWORLD_PATH}/RimWorldLinux

# Rest of build...
```

Build:

```bash
docker build -f Dockerfile.with-rimworld -t rimworld-ml-bridge:with-game .
```

### Pre-configured Steam Volume

Use Docker volume with RimWorld pre-installed:

```bash
# One-time setup
./docker/setup-rimworld-volume.sh /path/to/rimworld

# Use in tests
docker-compose up test
```

## Development Workflow

### Interactive Development

```bash
# Start dev container
docker-compose run --rm dev

# Inside container:
dotnet build RimworldMLBridge.sln
uv run python python/test_tcp_connection.py
```

### Build Only

```bash
docker-compose run --rm build
```

### Quick Test Iteration

```bash
# Keep container running
docker-compose up -d dev

# Run tests
docker-compose exec dev uv run python python/test_automated_suite.py --no-launch
```

## Troubleshooting

### RimWorld Not Found

```
ERROR: RimWorld not found at /opt/rimworld
```

**Solution**: Ensure RimWorld volume is mounted:

```bash
docker volume ls
docker volume inspect rimworld-data
```

### X Server Issues

```
ERROR: Unable to initialize display
```

**Solution**: Xvfb may not have started. Check logs:

```bash
docker logs <container-id>
```

### Permission Issues

```
ERROR: Cannot write to /app/test_results.txt
```

**Solution**: Ensure volume mount has correct permissions:

```bash
docker run --rm -v $(pwd):/app rimworld-ml-bridge ls -la /app
```

### Slow Startup

RimWorld takes 20-40s to start in headless mode. Increase timeout:

```python
# In test_automated_suite.py
client.connect(timeout=120)  # Increase timeout
```

## Performance Benchmarks

### Startup Times

- Container launch: ~5 seconds
- RimWorld headless start: ~20-30 seconds
- Test execution: ~30 seconds
- **Total**: ~1-1.5 minutes

### Resource Usage

- Memory: ~2-4 GB
- CPU: 1-2 cores
- Disk: ~5 GB (RimWorld + mod)

## Security Considerations

### Private Registry

If including RimWorld in image:

- Use private Docker registry (GitHub Container Registry, AWS ECR)
- Set repository to private
- Never push to Docker Hub public

### Secrets

Store Steam credentials (if needed) as secrets:

```yaml
env:
  STEAM_USERNAME: ${{ secrets.STEAM_USERNAME }}
  STEAM_PASSWORD: ${{ secrets.STEAM_PASSWORD }}
```

### Network Isolation

Container runs isolated by default:

- No inbound access required
- Only outbound for package downloads

## CI/CD Strategy

### Recommended Approach

**For Public Repos**:

1. Use Docker for build/unit tests
2. Use cached RimWorld volume
3. Manual RimWorld setup (one-time)

**For Private Repos**:

1. Include RimWorld in base image
2. Store in private registry
3. Full automation

### GitHub Actions Workflow

See: `.github/workflows/docker-integration-test.yml`

### Cost Comparison

| Method | Cost | Setup Time | Maintenance |
|--------|------|------------|-------------|
| Self-Hosted Runner | $50-100/mo | 2-3 hours | High |
| Cloud VM (on-demand) | $0.50/run | 1 hour | Medium |
| Docker (GitHub Actions) | **$0** | 30 min | **Low** |

## Alternatives Considered

### Windows Containers

**Pros**: Native Windows apps
**Cons**:

- Larger images (~10 GB)
- Slower startup
- Limited GitHub Actions support
- Requires Windows Server base

**Verdict**: Linux with headless mode is better

### WSL2 in Container

**Pros**: Windows compatibility layer
**Cons**:

- Complex setup
- Performance overhead
- Not supported on GitHub Actions

**Verdict**: Not practical

### SteamCMD Automation

**Pros**: Automated RimWorld download
**Cons**:

- Requires Steam credentials
- Against Steam ToS for CI
- Slow (~5 min download per run)

**Verdict**: Use cached volume instead

## Next Steps

1. ✅ Create Docker volume with RimWorld
2. ✅ Build Docker image
3. ✅ Run tests locally
4. ⏳ Update GitHub Actions workflow
5. ⏳ Test CI pipeline
6. ⏳ Document team workflow

## References

- [RimWorld Linux Headless Server](https://rimworldwiki.com/wiki/Dedicated_server)
- [Unity Headless Mode](https://docs.unity3d.com/Manual/CommandLineArguments.html)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [GitHub Actions Docker](https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions)

---

**Docker-based testing is now the recommended CI/CD approach!** 🐳
