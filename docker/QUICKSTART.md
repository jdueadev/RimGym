# Docker Testing - Quick Start Guide

## 🎯 Goal

Run **fully automated integration tests** in Docker containers instead of:

- ❌ Self-hosted Windows runners ($50-100/month)
- ❌ Cloud VMs ($0.50/run)
- ✅ **Docker on GitHub Actions (FREE!)**

## ⚡ 60-Second Setup

### 1. Install Docker

**Windows/Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)  
**Linux**: `sudo apt install docker.io docker-compose`

### 2. Download RimWorld Linux Version (Windows Only)

**⚠️ Windows users:** Docker uses Linux containers, so you need the Linux version of RimWorld.

**Option A: Using SteamCMD (Recommended)**

1. Download [SteamCMD](https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip)
2. Extract to `C:\steamcmd\`
3. Run this **single command** (forces Linux platform):

```powershell
cd C:\steamcmd
.\steamcmd.exe +@sSteamCmdForcePlatformType linux +force_install_dir C:\RimWorldLinux +login YOUR_STEAM_USERNAME +app_update 294100 validate +quit
```

**Important**: Replace `YOUR_STEAM_USERNAME` with your actual Steam username. You'll be prompted for your password.

**Option B: Using DepotDownloader (More Reliable)**

1. Install DepotDownloader via Windows Package Manager CLI (winget)

```powershell
winget install --exact --id SteamRE.DepotDownloader
```

2. Download RimWorld Linux version:

```powershell
.\DepotDownloader.exe -app 294100 -os linux -osarch 64 -username YOUR_STEAM_USERNAME -dir C:\RimWorldLinux
```

**Why depot 294101?** That's RimWorld's Linux depot specifically. This method is more reliable than SteamCMD's platform flag.

**Note**: RimWorld AppID is `294100`, Linux depot is `294101`. Download will be ~1.5GB and take 5-10 minutes.

### 3. Create RimWorld Volume

```powershell
# Point to the Linux version you just downloaded
.\docker\setup-rimworld-volume.ps1 "C:\RimWorldLinux"

# Verify
docker run --rm -v rimworld-data:/opt/rimworld alpine ls -la /opt/rimworld
# Should see: RimWorldLinux (executable), RimWorld_Data/, Mods/, etc.
```

### 3. Run Tests

```bash
docker-compose up test
```

**Expected output**:

```
✅ Game ready! (took 25s)
✅ PASS - Paused: Training 60 ticks (1153ms) | Inference 121 ticks (2014ms)
✅ PASS - 1x Speed: Training 60 ticks (1035ms) | Inference 122 ticks (2008ms)
✅ PASS - 2x Speed: Training 60 ticks (366ms) | Inference 345 ticks (2011ms)
✅ PASS - 3x Speed: Training 60 ticks (182ms) | Inference 724 ticks (2008ms)
```

**Total time**: ~2 minutes (startup + tests)

## 🔧 Common Commands

```bash
# Run tests
docker-compose up test

# Build only (no tests)
docker-compose run --rm build

# Interactive shell in container
docker-compose run --rm dev

# View test results
cat test_results.txt

# Clean up
docker-compose down
docker volume rm rimworld-data
```

## 🚀 GitHub Actions Integration

Once Docker works locally, enable CI:

1. **Commit Docker files**:

   ```bash
   git add Dockerfile docker/ docker-compose.yml .dockerignore
   git commit -m "Add Docker-based testing"
   git push
   ```

2. **Enable Docker workflow**:
   Edit `.github/workflows/docker-integration-test.yml`:

   ```yaml
   # Change line ~25 from:
   if: false  # Disabled
   # To:
   if: true   # Enabled
   ```

3. **Setup RimWorld cache** (one-time):
   - Download RimWorld Linux version
   - Create GitHub Actions cache:

     ```bash
     mkdir rimworld-cache
     cp -r /path/to/RimWorld/* rimworld-cache/
     git add rimworld-cache/
     git commit -m "Add RimWorld cache for CI"
     ```

4. **Push and watch**:

   ```bash
   git push origin main
   # Go to: https://github.com/YOUR_USERNAME/RimworldMLBridge/actions
   ```

## 🐛 Troubleshooting

### "RimWorld not found"

```bash
# Verify volume exists
docker volume ls
docker volume inspect rimworld-data

# Check volume contents
docker run --rm -v rimworld-data:/data alpine ls -la /data

# Re-create volume
./docker/setup-rimworld-volume.sh /path/to/RimWorld
```

### Tests timeout

```bash
# Increase timeout in test client
# Edit python/test_automated_suite.py
client.connect(timeout=120)  # Increase from 90
```

### Permission denied

```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker-compose up test
```

### Container fails to build

```bash
# Clear build cache
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
```

## 📊 Performance

| Stage | Time | Notes |
|-------|------|-------|
| Image build | ~5 min | Cached after first build |
| Container start | ~5 sec | Very fast |
| RimWorld startup | ~25 sec | Headless mode |
| Test execution | ~30 sec | 4 speed scenarios |
| **Total** | **~1 min** | After initial build |

## 🎓 What's Happening?

1. **Dockerfile**: Multi-stage build creates optimized image
   - Stage 1: Base (.NET + Python)
   - Stage 2: RimWorld base (Xvfb for headless Unity)
   - Stage 3: Builder (compile C# + Python)
   - Stage 4: Test runner (minimal runtime)

2. **Headless Mode**: RimWorld runs without graphics
   - `-batchmode`: No Unity editor
   - `-nographics`: No rendering
   - `-quicktest`: Fast dev mode startup
   - Xvfb: Virtual X server (Unity requires X11)

3. **Docker Volume**: Persistent RimWorld installation
   - Shared across container runs
   - No need to copy RimWorld every time
   - Can be cached in CI

## 🔐 Security Notes

**⚠️ Do NOT commit RimWorld files to public repos!**

Instead:

- Use Docker volumes (local testing)
- Use GitHub cache (CI)
- Use private Docker registry (if needed)

## 🆚 Comparison

| Method | Setup | Cost | Speed | Maintenance |
|--------|-------|------|-------|-------------|
| **Docker** | 5 min | $0 | 1-2 min | Low |
| Self-hosted | 2-3 hrs | $50-100/mo | 4-5 min | High |
| Cloud VM | 1 hr | $0.50/run | 5-7 min | Medium |

**Winner**: Docker 🏆

## 📚 Learn More

- [Full Docker Guide](README.md)
- [Dockerfile Reference](../Dockerfile)
- [GitHub Actions Workflow](../.github/workflows/docker-integration-test.yml)
- [RimWorld Headless Mode](https://rimworldwiki.com/wiki/Dedicated_server)

## ✅ Ready for Production

Once Docker tests pass:

1. ✅ Commit and push
2. ✅ Watch CI pass on GitHub Actions
3. ✅ Celebrate having zero-cost automated testing! 🎉

**You now have enterprise-grade CI/CD for a RimWorld mod!**
