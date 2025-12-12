# CI/CD Setup Guide

## Quick Start

This project has **full CI/CD automation** ready to deploy!

### 1. GitHub Actions (Already Configured)

✅ **4 workflows ready to use**:

1. **Build and Test** (`.github/workflows/build-and-test.yml`)
   - Runs on every push/PR
   - Builds C# mod
   - Runs Python tests
   - Optional integration tests (self-hosted runner)

2. **Docker Integration Tests** (`.github/workflows/docker-integration-test.yml`) **⭐ RECOMMENDED**
   - Runs on GitHub hosted runners (no self-hosting needed!)
   - Uses Docker containers with RimWorld headless mode
   - Fully automated, reproducible, portable
   - Zero cost on public repos

3. **PR Validation** (`.github/workflows/pr-validation.yml`)
   - Fast validation for pull requests
   - Formatting checks
   - Unit tests

4. **Release** (`.github/workflows/release.yml`)
   - Triggered by version tags
   - Creates GitHub releases
   - Packages mod for distribution

### 🐳 Recommended: Docker-Based Testing

**Why Docker?**

- ✅ No self-hosted runner needed
- ✅ Runs on GitHub Actions free tier
- ✅ Reproducible environment
- ✅ Portable (works locally + CI)
- ✅ Fast (~2 minutes total)

See: [docker/README.md](../../docker/README.md) for complete Docker setup guide

### 2. Enable Workflows

Workflows are already committed. They'll run automatically on your next push!

```powershell
# Push to trigger CI
git add .github/workflows/
git commit -m "Add CI/CD workflows"
git push origin main
```

Check: <https://github.com/YOUR_USERNAME/RimGym/actions>

### 3. Self-Hosted Runner (Optional - For Integration Tests)

Integration tests require RimWorld installed. Use self-hosted runner:

**Quick Setup**:

1. Go to: Settings → Actions → Runners → New self-hosted runner
2. Follow the setup instructions (Windows machine)
3. Set `RIMWORLD_PATH` environment variable on runner machine

**Full guide**: [.github/workflows/self-hosted-runner-setup.md](.github/workflows/self-hosted-runner-setup.md)

### 4. Test the Pipeline

**Option A: Manual Trigger (Recommended for first test)**

1. Go to Actions tab on GitHub
2. Select "Build and Test" workflow
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

**Option B: Commit Trigger**

```powershell
# Make a small change
echo "# Test CI" >> README.md
git add README.md
git commit -m "Test CI pipeline"
git push
```

Watch the workflow run: <https://github.com/YOUR_USERNAME/RimGym/actions>

### 5. Integration Test Trigger

Integration tests only run when:

- Manually triggered via workflow_dispatch
- Commit message contains `[test-integration]`

```powershell
git commit -m "Fix velocity tracking [test-integration]"
git push
```

## CI/CD Features

### ✅ What's Automated

**Build Validation**:

- C# compilation (Debug and Release)
- Native DLL exclusion check
- Python protobuf generation
- Code formatting validation

**Testing**:

- C# unit tests (26 tests)
- Python unit tests
- Integration tests (4 speed scenarios)
- Automated RimWorld launch and shutdown

**Artifact Management**:

- Compiled mod DLLs
- Test results
- Release packages

**Release Automation**:

- GitHub releases on version tags
- Automated changelog generation
- Distribution packages

### ⚡ Performance

Typical run times:

- **C# Build**: 1-2 minutes
- **Python Tests**: 30 seconds
- **Integration Tests**: 4-5 minutes (with RimWorld)
- **Total**: ~5-7 minutes per full pipeline run

### 🔧 Configuration

#### Enable Branch Protection

Require CI to pass before merging:

1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Check: "Require status checks to pass"
4. Select: `build-mod`, `test-python`
5. Save

#### Secrets (if needed later)

For Steam Workshop upload or other integrations:

1. Settings → Secrets → Actions
2. Add secrets as needed
3. Reference in workflows: `${{ secrets.SECRET_NAME }}`

## Monitoring

### Status Badges

Already added to README.md:

```markdown
[![Build](https://github.com/jmduea/RimGym/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/jmduea/RimGym/actions/workflows/build-and-test.yml)
```

### Email Notifications

GitHub sends email notifications on:

- Workflow failures
- First workflow success after failures

Configure: Profile → Settings → Notifications → Actions

### Slack/Discord Integration

Add webhook notifications (optional):

```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Troubleshooting

### Build Fails on GitHub but Passes Locally

**Cause**: Path differences or missing dependencies

**Solution**:

```powershell
# Test locally with exact CI commands
dotnet restore src\RimTCP\RimTCP\RimTCP.sln
dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release --no-restore
dotnet test tests\RimTCP.Tests\RimTCP.Tests.csproj -c Release
```

```

### Python Tests Fail on CI

**Cause**: Protobuf not generated

**Solution**: Workflow already handles this with `uv run python src/shared/python/src/generate_proto.py`

### Integration Tests Timeout

**Cause**: RimWorld taking too long to load

**Solution**: Increase timeout in workflow:

```yaml
timeout-minutes: 15  # Increase from 10
```

### Self-Hosted Runner Offline

**Check**:

```powershell
Get-Service actions.runner.*
```

**Restart**:

```powershell
Restart-Service actions.runner.*
```

## Release Process

### Create a Release

```powershell
# Tag version
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

**Automated**:

1. Workflow builds and tests
2. Creates GitHub release
3. Uploads mod package
4. Generates changelog

**Manual steps** (optional):

1. Edit release notes on GitHub
2. Upload to Steam Workshop (manual)

### Pre-Release Testing

Test before tagging:

```powershell
# Trigger release workflow with manual version
# Go to Actions → Release → Run workflow
# Enter version: 1.0.0-rc1
```

## Cost Optimization

### GitHub Actions Limits

Free tier:

- **Public repos**: Unlimited minutes
- **Private repos**: 2,000 minutes/month

### Reduce CI Usage

**Skip CI on docs changes**:

```yaml
on:
  push:
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

**Manual integration tests only**:

```yaml
if: github.event_name == 'workflow_dispatch'
```

## Next Steps

1. ✅ Push workflows to GitHub
2. ✅ Verify first workflow run passes
3. ⏳ (Optional) Set up self-hosted runner for integration tests
4. ⏳ Configure branch protection rules
5. ⏳ Add status badges to README (already done!)

## Support

- **GitHub Actions Docs**: <https://docs.github.com/en/actions>
- **Self-Hosted Runners**: [self-hosted-runner-setup.md](self-hosted-runner-setup.md)
- **Issues**: Open a GitHub issue with `[ci]` tag

---

**Your CI/CD pipeline is ready to go! Push to main and watch it run.** 🚀
