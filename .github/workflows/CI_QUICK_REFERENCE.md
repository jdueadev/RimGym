# CI/CD Quick Reference

## ✅ What's Already Set Up

Your CI/CD pipeline is **ready to use** with these workflows:

### 1. Build and Test (`build-and-test.yml`)

- **Triggers**: Push to main/develop, PRs, manual dispatch
- **Runs on**: GitHub hosted + self-hosted (optional)
- **Duration**: ~5-7 minutes
- **Jobs**:
  - ✅ Build C# mod
  - ✅ Python tests
  - ⏳ Integration tests (self-hosted only)

### 2. PR Validation (`pr-validation.yml`)

- **Triggers**: Pull requests
- **Runs on**: GitHub hosted
- **Duration**: ~3 minutes
- **Fast feedback** on PRs

### 3. Release (`release.yml`)

- **Triggers**: Version tags (`v*.*.*`)
- **Runs on**: GitHub hosted
- **Creates**: GitHub releases with packages

## 🚀 Quick Actions

### Run All Tests Locally

```powershell
# Full local CI simulation
dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release
dotnet test tests\RimTCP.Tests\RimTCP.Tests.csproj -c Release
uv sync
uv run python src/shared/python/src/generate_proto.py
uv run pytest src/RimGym/tests/
```

### Create a Release

```powershell
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
# Workflow automatically creates GitHub release
```

### Trigger Integration Tests

```powershell
# Option 1: Commit message
git commit -m "Fix bug [test-integration]"
git push

# Option 2: Manual (Actions tab → Build and Test → Run workflow)
```

### Skip CI on Docs Changes

```powershell
git commit -m "Update docs [skip ci]"
```

## 📊 Test Results

### Current Status

- **Phase III**: 100% complete ✅
- **Automated Tests**: 4 speeds (Paused, 1x, 2x, 3x)
- **Performance**: 0.003ms per colonist serialization
- **All tests passing**: ✅ Training mode, ✅ Inference mode, ✅ Velocity tracking

### Latest Results

```
✅ Paused:    Training 60 ticks (1153ms) | Inference 121 ticks (2014ms)
✅ 1x Speed:  Training 60 ticks (1035ms) | Inference 122 ticks (2008ms)
✅ 2x Speed:  Training 60 ticks (366ms)  | Inference 345 ticks (2011ms)
✅ 3x Speed:  Training 60 ticks (182ms)  | Inference 724 ticks (2008ms)
```

## 🔗 Links

- **Actions**: <https://github.com/jmduea/RimGym/actions>
- **Releases**: <https://github.com/jmduea/RimGym/releases>
- **Workflows**: [.github/workflows/](./)
- **Setup Guide**: [CI_SETUP_GUIDE.md](CI_SETUP_GUIDE.md)
- **Self-Hosted Runner**: [self-hosted-runner-setup.md](self-hosted-runner-setup.md)

## 🎯 Next Steps

Ready for **Phase IV**! No CI changes needed - workflows support new features automatically.

**Phase IV** (Triple-Threaded Client):

- Listener/Inference/Actor threads
- Hierarchical policy
- Interrupt handling

All will be tested by existing CI pipeline. Just push changes and tests run automatically! 🎉
