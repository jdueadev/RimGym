# Suggested Commands for RimGym Development

## System Commands (Windows PowerShell)
```powershell
# Navigation and file operations
cd path\to\dir          # Change directory
Get-ChildItem           # List directory (alias: ls, dir)
Get-Content file.txt    # Read file (alias: cat, type)
Remove-Item file.txt    # Delete file (alias: rm, del)
New-Item -ItemType File # Create file
Copy-Item src dest      # Copy file/folder
Move-Item src dest      # Move/rename

# Git commands (same as Unix)
git status              # Check status
git add .               # Stage all changes
git commit -m "msg"     # Commit
git push                # Push to remote
git pull                # Pull from remote
git branch              # List branches
git checkout branch     # Switch branch

# Search
Select-String "pattern" *.cs    # Grep equivalent
Get-ChildItem -Recurse -Filter "*.cs"  # Find files
```

## C# / .NET Development

### Build Commands
```powershell
# Build entire solution
dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release

# Build specific project
dotnet build src\RimTCP\RimTCP\RimTCP.csproj -c Release

# Build tests
dotnet build tests\RimTCP.Tests\RimTCP.Tests.csproj -c Release

# Run C# tests
dotnet test tests\RimTCP.Tests\RimTCP.Tests.csproj -c Release
```

### Verify Build (Check for native DLLs)
```powershell
Get-ChildItem src\RimTCP\1.6\Assemblies\*.dll | Where-Object { $_.Name -like "*csharp_ext*" }
# Should return nothing - native DLLs must be excluded!
```

### Output Location
- DLLs → `src/RimTCP/1.6/Assemblies/`

## Python Development

### IMPORTANT: Always Use UV (Never raw python/pip!)
```powershell
# Sync dependencies from pyproject.toml
uv sync

# Run any Python script
uv run python path/to/script.py

# Run Python module
uv run python -m module_name

# Generate protobuf Python code
uv run python src/shared/python/src/generate_proto.py
```

### Testing
```powershell
# Run all Python tests
uv run pytest src/RimGym/tests/

# Run specific test file
uv run pytest src/RimGym/tests/client/test_connection.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/RimGym/src
```

### Linting & Formatting
```powershell
# Format code with Ruff
uv run ruff format src/RimGym/

# Lint with Ruff
uv run ruff check src/RimGym/

# Type checking with MyPy
uv run mypy src/RimGym/src/
```

## Docker Commands

### Dashboard (RimStats)
```powershell
# Start dashboard stack
docker-compose -f src/RimStats/docker-compose.yml up -d

# View logs
docker-compose -f src/RimStats/docker-compose.yml logs -f

# Stop stack
docker-compose -f src/RimStats/docker-compose.yml down
```

### Full Integration
```powershell
# Build and start all containers
docker-compose up --build -d

# View container status
docker ps

# View specific container logs
docker logs rimgym-backend -f
```

## Documentation

### Build docs locally
```powershell
uv run mkdocs serve    # Starts at http://localhost:8000
uv run mkdocs build    # Build static site to site/
```

## Protobuf Schema

### Location
- Schema: `src/shared/Protos/rimgym.proto`
- C# Generated: Auto during build via Grpc.Tools
- Python Generated: `src/shared/python/src/rimgym_pb2.py`

### Regenerate Python Proto
```powershell
uv run python src/shared/python/src/generate_proto.py
```

## Environment Variables (Optional)
```powershell
# RimWorld paths for C# build
$env:RIMWORLD_DIR="C:\Program Files (x86)\Steam\steamapps\common\RimWorld"
$env:WORKSHOP_PATH="C:\Program Files (x86)\Steam\steamapps\workshop\content\294100"
$env:HARMONY_PATH="$env:WORKSHOP_PATH\2009463077\Current\Assemblies"
```
