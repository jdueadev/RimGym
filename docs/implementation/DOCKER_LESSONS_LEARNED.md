# Docker Debugging Session - Lessons Learned

**Date**: December 11, 2025  
**Duration**: ~4 hours of debugging  
**Outcome**: ✅ Complete success - all tests passing

## Executive Summary

After extensive troubleshooting with various approaches (software rendering, resolution changes, graphics mode experiments), we discovered the solution was simple: **return to the proven configuration with critical fixes for line endings and volume mounts**.

**Key Breakthrough**: The `-quicktest` flag in the original `entrypoint.sh` script was essential all along. This flag enables RimWorld's developer mode, which bypasses the problematic UI initialization that causes "Resolution too small (0x0)" errors.

## Chronology of Debugging Session

### 1. Initial Problem (Hour 0)

**Symptom**: Container exits immediately with code 137

**Logs Showed**:

```
Resolution too small (0x0)
NullReferenceException at TextureAtlas.ctor()
```

**Hypothesis**: Graphics initialization failing in headless mode

### 2. First Approach: Software Rendering (Hour 0.5-1.5)

**Attempt**: Force Mesa llvmpipe software rendering

**Configuration**:

```yaml
environment:
  - LIBGL_ALWAYS_SOFTWARE=1
  - MESA_GL_VERSION_OVERRIDE=3.3
  - GALLIUM_DRIVER=llvmpipe
```

**Result**: System hung, 2103% CPU usage

**Lesson**: Software rendering is computationally expensive and unnecessary. Unity can work with Xvfb's virtual framebuffer.

### 3. Second Approach: Resolution Experiments (Hour 1.5-2.5)

**Attempts**:

- 1920x1080x24 (HD resolution)
- 800x600x24 (standard VGA)
- 640x480x16 (minimal)
- Created Unity PlayerPrefs with explicit settings

**Results**: Same "Resolution too small (0x0)" error every time

**Lesson**: The problem wasn't the screen size or resolution. Unity was crashing before it could read any configuration.

### 4. Third Approach: Full Graphics Mode (Hour 2.5-3)

**Attempt**: Remove `-nographics` flag, keep only `-batchmode`

**Configuration**:

```bash
./RimWorldLinux -batchmode -logfile /app/rimworld.log
```

**Result**: Different error - GLX/OpenGL issues, still crashed

**Lesson**: Xvfb alone isn't enough. Need both `-nographics` AND something else.

### 5. Research Breakthrough (Hour 3)

**Discovery**: Found RimWorld Multiplayer Headless Server documentation:
> "Don't use 'batchmode -nographics' on linux" (due to autosave issues)

**Insight**: Community has encountered these issues before with RimWorld on Linux.

**User Contribution**: "we were able to get rimworld running on the docker container before without software rendering"

**Direction Change**: Return to original working configuration

### 6. Root Cause Analysis (Hour 3-3.5)

**Investigation of Original `entrypoint.sh`**:

```bash
./RimWorldLinux -batchmode -nographics -quicktest -logfile /app/rimworld.log
```

**The Missing Piece**: `-quicktest` flag

- Enables RimWorld developer mode
- Bypasses problematic UI initialization
- Allows headless operation without graphics crashes

**Why We Missed It**: Focused on docker-compose.yml inline commands instead of testing the existing entrypoint script.

### 7. Critical Fixes (Hour 3.5-4)

**Issue 1: Line Endings**

```bash
# Error: entrypoint.sh: not found
# File exists but bash can't execute it
```

**Root Cause**: Windows CRLF (0x0D 0x0A) vs Linux LF (0x0A)

**Fix**:

```powershell
(Get-Content scripts\entrypoint.sh -Raw) -replace "`r`n", "`n" | 
  Set-Content scripts\entrypoint.sh -NoNewline
```

**Issue 2: Volume Mount Conflicts**

```
Input/output error on .venv/lib/python3.11/site-packages
```

**Root Cause**: Host `.venv` (Windows) conflicting with container `.venv` (Linux)

**Fix**: Changed from:

```yaml
volumes:
  - .:/app  # BAD: Mounts everything including .venv
```

To:

```yaml
volumes:
  - ./src/RimGym:/app/src/RimGym  # GOOD: Selective mounts
  - ./src/shared:/app/src/shared
  - rimworld-data:/opt/rimworld
```

### 8. Success (Hour 4)

**Configuration**:

- Used `entrypoint.sh` script with `-quicktest` flag
- Fixed line endings to LF
- Selective volume mounts
- No software rendering

**Results**:

```
✅ Total Tests: 4
✅ Passed: 4
✅ Failed: 0
✓ Paused: Training 60 ticks, Inference 116 ticks
✓ 1x Speed: Training 60 ticks in 1095ms, Inference 115 ticks
✓ 2x Speed: Training 60 ticks in 364ms, Inference 346 ticks
✓ 3x Speed: Training 60 ticks in 182ms, Inference 691 ticks
Exit code: 0
```

## Key Learnings

### 1. Test the Proven Path First

**Mistake**: Immediately started customizing docker-compose.yml with inline commands.

**Better Approach**:

1. Test existing `entrypoint.sh` script first
2. Verify it works as-is
3. Only then customize if needed

**Why It Matters**: The original maintainers likely encountered and solved these issues already. Their configuration is battle-tested.

### 2. Platform Differences Are Real

**Windows Development Traps**:

- Line endings (CRLF vs LF)
- File permissions (777 vs 755)
- Path separators (\ vs /)
- File locking behavior

**Solutions**:

- Use `.gitattributes`: `*.sh text eol=lf`
- Test in target platform (Linux container) early
- Document platform-specific requirements
- Use cross-platform tools (e.g., UV instead of pip)

### 3. Volume Mounts Need Design

**Anti-Pattern**: Mount everything for convenience

```yaml
volumes:
  - .:/app  # Seems simple but causes issues
```

**Best Practice**: Mount only what's needed

```yaml
volumes:
  - ./python:/app/python    # Test scripts
  - ./Protos:/app/Protos    # Protobuf files
  - rimworld-data:/opt/rimworld  # Isolated game data
```

**Why**:

- Avoids file conflicts
- Clearer dependency tracking
- Better performance
- Easier to reason about

### 4. Community Documentation Is Valuable

**Discovery Process**:

1. Official RimWorld docs don't cover headless mode
2. Found RimWorld Multiplayer project docs
3. They mentioned `-batchmode -nographics` issues on Linux
4. This led to investigating the `-quicktest` solution

**Lesson**: For games and commercial software, community mods/projects often have the best operational documentation.

### 5. Don't Over-Engineer Solutions

**Progression**:

1. Simple error → Complex solution (software rendering)
2. Complex solution fails → More complex solution (custom prefs)
3. Everything fails → Return to simple solution (original config)
4. Simple solution works with minor fixes

**Pattern**: Often the simplest solution is correct, we just need to fix its prerequisites (line endings, mounts).

### 6. Debugging Is Iterative Discovery

**What Worked**:

- Systematic testing of hypotheses
- Capturing full logs at each step
- Researching similar issues
- Asking user for historical context
- Returning to known-good state

**What Didn't Work**:

- Jumping to complex solutions
- Making multiple changes at once
- Assuming cross-platform compatibility
- Ignoring existing documentation/scripts

### 7. Document Everything

**Why This Document Exists**: So the next person (including future us) doesn't repeat this 4-hour debugging journey.

**What to Document**:

- ✅ What didn't work (and why)
- ✅ What did work (and why)
- ✅ Critical configuration requirements
- ✅ Common pitfalls
- ✅ Troubleshooting steps

## Technical Deep Dives

### Why `-quicktest` Works

**Normal RimWorld Startup**:

1. Initialize Unity rendering
2. Load texture atlases
3. Initialize UI system
4. Load mods
5. Start game

**Problem**: Steps 1-3 fail in headless mode before mods load.

**With `-quicktest`**:

1. Skip normal UI initialization
2. Enable dev mode features
3. Load mods early
4. Skip problematic startup checks
5. Start game with minimal UI

**Result**: Mod loads before crash can occur, RimTCP can hook into system successfully.

### Line Endings Deep Dive

**Why CRLF Causes Issues**:

```bash
#!/bin/bash\r
# Bash interpreter sees: "#!/bin/bash^M" (^M is CR character)
# Doesn't match any known interpreter path
# Result: "not found" error
```

**Detection**:

```bash
# View file with visible line endings
cat -A entrypoint.sh | head -1
# CRLF: #!/bin/bash^M$
# LF:   #!/bin/bash$
```

**Prevention**:

```gitattributes
# .gitattributes file
*.sh text eol=lf
*.ps1 text eol=crlf
```

### Volume Mount Internals

**When Mounting `.:/app`**:

```
Host (Windows)              Container (Linux)
├── .venv/                  ├── .venv/  (mounted from host!)
│   └── Lib/                │   └── Lib/ (Windows paths)
│       └── site-packages/  │       └── site-packages/
│           └── *.pyd       │           └── *.pyd (Windows DLLs!)
```

**Problem**: Container tries to load Windows DLLs in Linux environment.

**Solution**: Separate volumes

```
Host (Windows)              Container (Linux)
├── .venv/ (NOT mounted)    ├── .venv/ (container's own)
├── python/ (mounted)       ├── python/ (from host)
└── Protos/ (mounted)       └── Protos/ (from host)
```

## Preventive Measures

### Development Checklist

Before committing Docker changes:

- [ ] Test in Linux container (not just Windows)
- [ ] Verify shell scripts have LF line endings
- [ ] Review volume mounts (minimal necessary)
- [ ] Check for platform-specific dependencies
- [ ] Document any platform-specific requirements
- [ ] Add troubleshooting notes for common issues

### Code Review Checklist

When reviewing Docker PRs:

- [ ] Are line endings correct for target platform?
- [ ] Are volume mounts minimal and necessary?
- [ ] Are file permissions appropriate? (shell scripts +x)
- [ ] Are there hardcoded paths that won't work cross-platform?
- [ ] Is documentation updated for any config changes?
- [ ] Are there health checks for critical services?

### Testing Checklist

For Docker-based tests:

- [ ] Does container start successfully?
- [ ] Do logs show expected startup sequence?
- [ ] Are all required ports accessible?
- [ ] Does health check pass?
- [ ] Do tests complete with exit code 0?
- [ ] Are results reproducible across machines?

## References

### Internal Documentation

- [PHASE_IV_7_DOCKER_INTEGRATION.md](PHASE_IV_7_DOCKER_INTEGRATION.md) - Full implementation details
- [docker/TROUBLESHOOTING.md](../../docker/TROUBLESHOOTING.md) - Troubleshooting guide
- [docker/QUICKSTART.md](../../docker/QUICKSTART.md) - Setup guide
- [docker/README.md](../../docker/README.md) - Comprehensive reference

### External Resources

- [RimWorld Multiplayer Headless Server](https://github.com/Zetrith/Multiplayer) - Community headless mode
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/) - Official Docker docs
- [Git Line Endings](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration#_core_autocrlf) - Cross-platform Git

### Tools Used

- Docker Desktop 4.x (Windows)
- PowerShell 7.x for scripting
- Git Bash for Unix commands on Windows
- UV for Python package management
- Visual Studio Code for editing

## Conclusion

**Time Investment**: 4 hours debugging  
**Time Saved**: Countless hours for future developers  
**ROI**: Infinite (prevented repeated debugging sessions)

**The One Thing**: When Docker containers fail, start by verifying the basics:

1. Line endings (LF for Linux)
2. Volume mounts (minimal, specific)
3. Proven configurations (test before customizing)

**Final Wisdom**: The best debugging tool is often a working example from the past. Don't reinvent the wheel until you understand why the existing wheel doesn't turn.
