# RimWorld ML Bridge - AI Coding Agent Instructions

## Project Overview
This is a RimWorld mod that enables machine learning agents to interact with the game through a **TCP + Protocol Buffers** interface. The mod bridges Unity/C# game code with Python ML training frameworks for reinforcement learning research.

**Critical Context**: This started as gRPC but migrated to raw TCP because RimWorld's Mono runtime cannot load native C++ libraries (`grpc_csharp_ext.dll`). See `NATIVE_DLL_FIX.md` and `TCP_PROTOBUF_IMPLEMENTATION.md` for the evolution.

**Real-Time Architecture**: The project implements a **Hybrid Valve** system supporting both synchronous (training) and asynchronous (inference) modes. This addresses the "Frame Slip" problem where the game continues running while the agent processes observations. See `REAL_TIME_ARCHITECTURE_UPDATE.md` for the complete design.

**RIMAPI Integration**: Currently integrating high-fidelity data extraction logic from the RIMAPI project via an "Organ Transplant" strategy - porting robust Services (ColonistService, MapService) and mapping to lightweight Protobuf messages.

## Architecture & Communication Flow

```
Python RL Agent (TCP Client)  ←→  RimWorld Mod (TCP Server)
   Port 50051, Protobuf              Background Thread → Main Thread

Dual Operating Modes:
  Training Mode:   Game pauses → Agent thinks → STEP command → Game runs N ticks
  Inference Mode:  Game runs freely → Agent queries state asynchronously → Issues intents
```

### The Threading Model (Critical!)
RimWorld runs on Unity's single-threaded architecture. **All Unity/RimWorld API calls MUST execute on the main thread**. The mod implements this pattern:

1. **Background Thread**: `TcpProtobufServer` listens for connections and reads messages
2. **Thread-Safe Queue**: Commands are enqueued via `ConcurrentQueue<CommandMessage>`
3. **Main Thread Processing**: `Root_Update_Patch` (Harmony postfix on `Root.Update()`) dequeues and processes commands
4. **Response Queue**: Results are enqueued and sent back by background thread
5. **Server-Side Validation**: Actions are validated before execution (pawn alive? target reachable?) to handle latency/stale data

**Never access `Current.Game`, `Find.*`, or any `Pawn`/`Thing` from background threads!**

### The Hybrid Valve (Dual-Mode Operation)
- **Training Mode (Synchronous)**: `TickManager` is hijacked. Game strictly pauses between steps, waits for STEP command. Ensures deterministic, reproducible training.
- **Inference Mode (Asynchronous)**: `TickManager` runs freely at normal speed. Agent queries state via QUERY_STATE without blocking game. Tests real-time performance under latency.

Implementation: `TickPatch.cs` checks a mode flag. In training mode, prefix patch returns `false` to skip original `DoSingleTick()` unless agent sends STEP.

### Protocol Buffers Schema (`Protos/mlbridge.proto`)
- **CommandMessage**: Agent → Game (STEP, RESET, QUERY_STATE, EXECUTE_ACTION)
- **StateMessage**: Game → Agent (frame_id, entities, global state, timestamps)
- **Entity**: Represents pawns with health, needs, position, velocity vectors, current job
- **Action**: Intent-based commands (ExecuteJob with ThingID, not fragile coordinates)
  - Uses semantic intents: `ATTACK(targetID=402)` not `ATTACK(x=10, y=15)`
  - C# validates: Is pawn drafted? Is target alive? Is path reachable?
  - Failures send FAILURE_SIGNAL events for agent replanning

**Performance Optimizations**:
- Messages use length-prefixed framing: 4-byte big-endian length header + serialized protobuf bytes
- Delta compression for map data: Only changed cells sent in async mode
- Velocity vectors in Entity messages allow agent to extrapolate positions under latency

## Build System

### C# Build (.NET Framework 4.8)
**Output Directory**: `1.6/Assemblies/` (RimWorld 1.6 mod structure)

**Critical .csproj Settings**:
- `<OutputPath>..\1.6\Assemblies</OutputPath>` - Direct output to mod structure
- `<DebugType>none</DebugType>` - No PDB files for mods
- `ExcludeAssets="native"` on Grpc.Core - Prevents native DLL inclusion
- Post-build target `RemoveNativeDlls` - Safety cleanup for any native libraries

**Required References**:
- RimWorld: `Assembly-CSharp.dll` from `$(RimWorldPath)`
- Unity: `UnityEngine.CoreModule.dll`
- Harmony: `0Harmony.dll` from workshop mod #2009463077
- Protobuf: `Google.Protobuf` NuGet (managed only)

**Path Variables**: Set `$(RimWorldPath)`, `$(WorkshopPath)`, `$(HarmonyPath)` in `.csproj` or environment

### Python Build
Run `python/generate_proto.py` to generate `mlbridge_pb2.py` from the `.proto` file. Only requires `protobuf` package (NOT `grpcio`).

### Build Commands
```powershell
# Full build
dotnet build RimworldMLBridge.sln -c Release

# Verify no native DLLs in output
Get-ChildItem 1.6\Assemblies\*.dll | Where-Object { $_.Name -like "*csharp_ext*" }
# Should return nothing
```

## Harmony Patching Strategy

### Current Patches
1. **`Root_Update_Patch`** (Postfix on `Verse.Root.Update()`)
   - Purpose: Process queued TCP commands on main thread
   - Called every frame when mod is active
   - Handles: `TcpProtobufServer.ProcessCommands()`
   - Validates and executes actions from queue, handles failures gracefully

2. **`TickManager_DoSingleTick_Patch`** (Prefix + Postfix in `TickPatch.cs`)
   - **Prefix**: In training mode, returns `false` to block original method unless STEP command received
   - **Postfix**: Logs ticks, sends state snapshots back to agent
   - Implements the "Hybrid Valve" - controls whether game advances or waits for agent
   - Mode toggle: Check `MlBridgeMod.TrainingMode` flag to switch between sync/async

### Harmony Best Practices for This Mod
- Use `[StaticConstructorOnStartup]` for mod initialization (see `MlBridgeMod`)
- Harmony ID: `"com.jmduea.rimworldmlbridge"`
- Always catch exceptions in patch bodies to avoid crashing RimWorld
- Log all important events with `[MLBridge]` prefix for easy filtering

## State Extraction Pattern

### Getting Game State (Evolving toward RIMAPI Integration)
Current implementation in `TcpProtobufServer.cs` provides rich state via adapters. Uses ColonistAdapter, MapAdapter, IncidentAdapter, and WorldAdapter:

```csharp
// Current basic extraction
if (Current.Game != null && Find.CurrentMap != null)
{
    // Access colonist pawns
    foreach (var pawn in Find.CurrentMap.mapPawns.FreeColonistsSpawned)
    {
        // Extract position, health, needs, current job
        var health = pawn.health.summaryHealth.SummaryHealthPercent;
        var job = pawn.CurJobDef?.defName ?? "None";
        
        // Check for null on needs subsystem
        if (pawn.needs != null)
        {
            var mood = pawn.needs.mood?.CurLevel ?? 0;
        }
    }
}
```

**RIMAPI Integration (Planned)**:
- Port `ColonistService.cs`, `MapService.cs`, `WorldService.cs` from RIMAPI
- Strip HTTP/JSON layers, use raw C# DTOs
- Create `ProtobufAdapter` class to map DTOs → Protobuf messages (<1ms serialization)
- Provides: Full skill trees, relationships, memory states, terrain tensors, building data

**Key RimWorld APIs**:
- `Find.CurrentMap`: Current active map
- `Find.TickManager`: Game time/speed control
- `Find.WorldGrid`: World coordinates
- `Current.Game`: Game session (null in main menu)
- Pawns: `mapPawns.FreeColonistsSpawned`, `AllPawnsSpawned`

## Common Development Tasks

### Adding New Protobuf Messages
1. Edit `Protos/mlbridge.proto`
2. Rebuild C# (Grpc.Tools auto-generates C# from `.proto`)
3. Run `python/generate_proto.py` for Python bindings
4. Update `TcpProtobufServer.ProcessCommands()` to handle new command types

### Porting RIMAPI Services ("Organ Transplant" Strategy)
1. Copy service class from RIMAPI `Services/` folder (e.g., `ColonistService.cs`)
2. Remove HTTP controller dependencies and JSON serialization
3. Keep the robust data extraction logic and DTO classes
4. Create mapping methods in `ProtobufAdapter.cs` to convert DTOs → Protobuf messages
5. Call service methods from `TcpProtobufServer.ProcessCommands()` on main thread
6. Test serialization performance (target <1ms for full state)

### Configuring Training vs Inference Mode
1. Set `MlBridgeMod.TrainingMode = true/false` flag
2. In training mode: Game pauses automatically, only advances on STEP commands
3. In inference mode: Game runs at normal speed, agent polls asynchronously
4. Test both modes: Training for deterministic learning, Inference for real-time robustness

### Testing the Connection
1. Start RimWorld with mod enabled, load a save
2. Check log: `[MLBridge] TCP+Protobuf server started successfully!`
3. Run: `python python/test_tcp_connection.py`
4. Should print colonist count, health, and step through 1 second (60 ticks)

### Debugging Threading Issues
If you see `NullReferenceException` on Unity objects:
- Check if code runs on background thread (bad!)
- Move logic into `TcpProtobufServer.ProcessCommands()` (main thread)
- Use `ConcurrentQueue` to pass data between threads

## Known Limitations & Future Work

**Current State (Phase I Complete)**:
- ✅ TCP server with protobuf serialization
- ✅ Game state observation (basic colonist data)
- ✅ Thread-safe main thread dispatching
- ✅ Step command (advance N ticks)

**Phase II (Current Priority - "Organ Transplant")**:
- 🔄 Port RIMAPI Services for high-fidelity data extraction
- 🔄 Implement ProtobufAdapter for efficient DTO → Protobuf mapping
- 🔄 Define intent-based Action messages in protobuf
- 🔄 Add server-side action validation and failure handling

**Phase III (Hybrid Valve)**:
- ⏳ Implement AsyncMode toggle in C#
- ⏳ Complete TickManager.DoSingleTick prefix patch for mode switching
- ⏳ Add delta compression for real-time map updates
- ⏳ Implement velocity vectors and timestamp tracking

**Phase IV (Python Client)**:
- ⏳ Develop triple-threaded SpectatorClient.py (Listener/Inference/Actor threads)
- ⏳ Implement hierarchical policy (Executive/Reflex layers)
- ⏳ Add interrupt event handling (raids, fires, mental breaks)

**Known Issues**:
- If native gRPC DLLs slip into `1.6/Assemblies/`, RimWorld crashes with `BadImageFormatException`
- Solution: Post-build cleanup target in `.csproj` must run successfully

## File Organization

```
RimworldMLBridge/
├── About/About.xml                 # Mod metadata (name, version, Harmony dependency)
├── 1.6/Assemblies/                 # Build output (DLLs go here)
├── Protos/mlbridge.proto           # Protocol Buffers schema (single source of truth)
├── RimworldMLBridge/               # C# source
│   ├── RimworldMLBridge.cs        # Mod entry, Harmony init, server startup
│   ├── TcpProtobufServer.cs       # TCP listener, message framing, queue management
│   ├── GrpcService.cs             # LEGACY: gRPC service (not used anymore but has state extraction logic)
│   ├── TickPatch.cs               # Harmony patches on game tick
│   └── *.csproj                   # Build config
└── python/
    ├── mlbridge_pb2.py            # Generated protobuf (gitignored)
    ├── generate_proto.py          # Generator script
    └── test_tcp_connection.py     # Test client

Documentation:
├── ARCHITECTURE.md                      # Original deep RL theory and roadmap
├── REAL_TIME_ARCHITECTURE_UPDATE.md    # Current: Real-time hybrid architecture, RIMAPI integration
├── TCP_PROTOBUF_IMPLEMENTATION.md      # Current implementation details
├── NATIVE_DLL_FIX.md                   # Why we abandoned gRPC
└── GRPC_MIGRATION.md                   # Historical: when we tried gRPC
```

## Code Style Conventions
- Use `[MLBridge]` prefix in all logs for easy filtering
- Wrap Unity API calls in try-catch with graceful degradation
- Check `Current.Game != null` before accessing game state
- Use `?.` null-conditional operator extensively for RimWorld objects
- Comment threading boundaries (main thread vs background thread)

## Quick Reference: Key Classes
- **`MlBridgeMod`**: Static constructor, Harmony init, server startup, mode flags
- **`TcpProtobufServer`**: TCP listener, framing, queues, main thread processing, action validation
- **`Root_Update_Patch`**: Harmony patch that calls `ProcessCommands()` every frame
- **`TickManager_DoSingleTick_Patch`**: Implements hybrid valve for training/inference mode switching
- **`GrpcService`**: Has useful state extraction code (GetState method) even though gRPC isn't used
- **`ProtobufAdapter`** (Planned): Maps RIMAPI DTOs to Protobuf messages
- **RIMAPI Services** (Being Ported): ColonistService, MapService, WorldService for rich data
- **`MLBridgeClient`** (Python): Length-prefixed protobuf send/receive over TCP
- **`SpectatorClient`** (Planned): Triple-threaded async client (Listener/Inference/Actor)

## When You Need to Know More
- **RimWorld modding basics**: Check official docs at https://rimworldwiki.com/wiki/Modding_Tutorials
- **Harmony patching**: https://harmony.pardeike.net/
- **Protocol Buffers**: https://protobuf.dev/
- **Unity threading**: Unity forbids accessing GameObject/Transform from background threads

---
applyTo: "**/*.py" 
---
# Python Execution and Package Management Instructions

## ⚠️ CRITICAL: UV-ONLY Policy
**NEVER use `python`, `pip`, or `venv` commands directly. ALWAYS use `uv` equivalents.**

## Quick Command Reference

### Running Code (NEVER use `python` directly)
-   ❌ `python script.py` → ✅ `uv run script.py`
-   ❌ `python -m module` → ✅ `uv run python -m module`
-   ❌ `python -c "code"` → ✅ `uv run python -c "code"`
-   ❌ Interactive: `python` → ✅ `uv run python`

### Package Management (NEVER use `pip` directly)
-   ❌ `pip install package` → ✅ `uv add package`
-   ❌ `pip install -r requirements.txt` → ✅ `uv sync` (preferred) or `uv pip install -r requirements.txt`
-   ❌ `pip uninstall package` → ✅ `uv remove package`
-   ❌ `pip list` → ✅ `uv pip list`
-   ❌ `pip freeze` → ✅ `uv pip freeze`

### Testing (NEVER activate venv or use python directly)
-   ❌ `python -m pytest` → ✅ `uv run pytest`
-   ❌ `pytest tests/` → ✅ `uv run pytest tests/`
-   ❌ `.venv/Scripts/activate && pytest` → ✅ `uv run pytest`

### Project Management
-   **Initialize project**: `uv init`
-   **Sync dependencies**: `uv sync` (installs from pyproject.toml/uv.lock)
-   **Update lock file**: `uv lock --upgrade`
-   **Add dev dependency**: `uv add --dev package`

### Environment Management (NEVER use `venv` directly)
-   ❌ `python -m venv .venv` → ✅ `uv venv`
-   ❌ `source .venv/bin/activate` → ✅ Not needed! Use `uv run` instead
-   **DO NOT manually activate virtual environments** - `uv run` handles this automatically

## Why UV?
-   **10-100x faster** than pip
-   **Automatic dependency resolution** without conflicts
-   **Built-in project management** with pyproject.toml
-   **No manual venv activation** needed

## When In Doubt
-   Prefix ANY Python command with `uv run`
-   For package operations, use `uv add`/`uv remove`
-   See `uv-python-usage-guide.instructions.md` for comprehensive documentation

## Common Mistakes to Avoid
1. ❌ Running raw `python` or `pytest` commands
2. ❌ Using `pip install` for adding dependencies
3. ❌ Manually activating virtual environments
4. ❌ Using `requirements.txt` instead of `pyproject.toml` + `uv.lock`
5. ❌ Forgetting `uv run` prefix for scripts