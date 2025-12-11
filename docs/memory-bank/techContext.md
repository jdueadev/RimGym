# Technical Context

## Technologies

### C# / .NET

- **Framework**: .NET Framework 4.8 (RimWorld compatibility)
- **Language Version**: C# 7.3
- **IDE**: Visual Studio 2019+, or Rider
- **Version**: 0.5.0
- **Harmony ID**: `com.jmduea.rimtcp`

### Key Dependencies

```xml
<PackageReference Include="Google.Protobuf" Version="3.21.12" />
<PackageReference Include="Grpc.Tools" Version="2.46.6" PrivateAssets="All" />
```

**Note**: Grpc.Core is NOT used at runtime - only Grpc.Tools for proto compilation.

### Python

- **Version**: 3.11+ (3.8+ minimum)
- **Package Manager**: UV (required, not pip)
- **Version**: 0.5.0
- **Key Dependencies**: protobuf, gymnasium, numpy

### Protocol Buffers

- **Schema**: `src/shared/Protos/rimgym.proto`
- **C# Generation**: Auto via Grpc.Tools during build
- **Python Generation**: `uv run python src/shared/python/src/generate_proto.py`

---

## Project Structure

```
src/
├── RimTCP/              # C# RimWorld mod
│   ├── RimTCP/          # Source code
│   │   ├── Adapters/    # DTO → Protobuf converters
│   │   ├── DTOs/        # Data transfer objects
│   │   ├── Services/    # Game data extraction
│   │   └── Diagnostics/ # Performance profiling
│   └── 1.6/Assemblies/  # Build output
├── RimGym/              # Python client
│   ├── src/
│   │   ├── client/      # TCP client, threading
│   │   ├── gym_env/     # Gymnasium environment
│   │   └── policies/    # RL policies
│   └── tests/
├── RimStats/            # Dashboard
│   ├── backend/         # FastAPI
│   └── frontend/        # React + TypeScript
└── shared/
    └── Protos/          # rimgym.proto schema
```

---

## Build Commands

### C# Build

```powershell
# Full solution build
dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release

# Tests
dotnet test tests\RimTCP.Tests\RimTCP.Tests.csproj -c Release
```

**Output**: `src/RimTCP/1.6/Assemblies/RimTCP.dll`

### Python Build

```powershell
# Sync dependencies
uv sync

# Generate protobuf
uv run python src/shared/python/src/generate_proto.py

# Run tests
uv run pytest src/RimGym/tests/

# Lint/format
uv run ruff format src/RimGym/
uv run ruff check src/RimGym/
```

### Docker

```powershell
# Dashboard
docker-compose -f src/RimStats/docker-compose.yml up -d

# Full integration
docker-compose up -d
```

---

## Environment Variables (Optional)

```powershell
# RimWorld paths for C# build
$env:RIMWORLD_DIR="C:\Program Files (x86)\Steam\steamapps\common\RimWorld"
$env:WORKSHOP_PATH="C:\Program Files (x86)\Steam\steamapps\workshop\content\294100"
$env:HARMONY_PATH="$env:WORKSHOP_PATH\2009463077\Current\Assemblies"
```

---

## Technical Constraints

### Unity/RimWorld Limitations

1. **Single-Threaded**: All Unity API calls MUST be on main thread
2. **Mono Runtime**: Cannot load native C++ libraries (hence TCP not gRPC)
3. **Mod Loading**: DLLs must be in `1.6/Assemblies/` folder
4. **Harmony Limitations**: Prefix patches can block original methods

### Performance Targets (All Achieved ✅)

| Metric | Target | Actual |
|--------|--------|--------|
| Serialization | <1ms | 0.003ms |
| Throughput | >1000 TPS | ✅ |
| Latency | <100ms | ✅ |
| Memory | <500MB | ✅ |

---

## Known Issues & Workarounds

### Native DLL Loading

**Issue**: RimWorld's Mono cannot load `grpc_csharp_ext.dll`  
**Solution**: Use raw TCP with managed protobuf only

### Main Thread Access

**Issue**: Background threads can't access Unity APIs  
**Solution**: Queue commands via `ConcurrentQueue`, process on `Root.Update()`

### Hot Reload

**Issue**: Mod code changes require RimWorld restart  
**Workaround**: Use Harmony debug logging and test in isolation

### Protobuf Schema Evolution

**Issue**: Breaking changes require coordinated updates  
**Best Practice**: Use field numbers carefully, never reuse deleted fields
