# Task Completion Checklist

When completing a task, follow this checklist to ensure quality and consistency.

## Before Marking Complete

### 1. Code Quality
- [ ] Code follows style conventions (see `style_and_conventions.md`)
- [ ] No compilation errors (`dotnet build` / `uv run python -m py_compile`)
- [ ] No linting errors
  - C#: Visual Studio / Rider warnings addressed
  - Python: `uv run ruff check src/RimGym/`

### 2. Type Safety
- [ ] Python: Type hints on all new public functions
- [ ] Python: `uv run mypy src/RimGym/src/` passes (or known warnings documented)
- [ ] C#: Nullable reference types handled properly

### 3. Testing
- [ ] Existing tests still pass
  - C#: `dotnet test tests\RimTCP.Tests\RimTCP.Tests.csproj`
  - Python: `uv run pytest src/RimGym/tests/`
- [ ] New functionality has tests (if applicable)
- [ ] Edge cases considered

### 4. Documentation
- [ ] Code comments for non-obvious logic (especially "why", not "what")
- [ ] Docstrings for new public APIs
- [ ] README or guide updates if user-facing changes

### 5. Build Verification
- [ ] Full build succeeds: `dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release`
- [ ] No native DLLs in output (critical!):
  ```powershell
  Get-ChildItem src\RimTCP\1.6\Assemblies\*.dll | Where-Object { $_.Name -like "*csharp_ext*" }
  ```
- [ ] Python imports work: `uv run python -c "from src.client import SpectatorClient"`

## Quick Commands Summary

```powershell
# Build all
dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release

# Test all
dotnet test tests\RimTCP.Tests\RimTCP.Tests.csproj
uv run pytest src/RimGym/tests/

# Lint/Format Python
uv run ruff format src/RimGym/
uv run ruff check src/RimGym/
uv run mypy src/RimGym/src/
```

## Performance Considerations
- State serialization should be <1ms (currently ~0.003ms per colonist)
- New Protobuf messages should be profiled
- No blocking operations in hot paths

## Threading Safety (C# Specific)
- [ ] No Unity/RimWorld API calls from background threads
- [ ] ConcurrentQueue used for cross-thread communication
- [ ] Main thread processing via Root_Update_Patch

## Memory Bank Updates
For significant changes, update relevant Memory Bank files:
- `docs/memory-bank/activeContext.md` - Current work focus
- `docs/memory-bank/progress.md` - What's completed
- `docs/memory-bank/tasks/_index.md` - Task status
