# RimGym Monorepo - AI Coding Agent Instructions

## Project Overview
This is a repository containing all of the projects necessary to enable reinforcement learning research with RimWorld through the standard Gymnasium interface via custom Gymnasisum environment `RimGymEnv`.
The key components are:

- **RimWorld Mod (`RimTCP`)**: A mod that exposes a TCP server interface using Protocol Buffers for communication. It supports both synchronous (training) and asynchronous (inference) modes via a hybrid valve system.

- **Custom Gymnasium Environment (`rimgym`)**: A Gymnasium environment that connects to the RimWorld mod over TCP, sending commands and receiving state updates. It provides standard Gym interfaces for RL algorithms.

- **Real Time Observability Dashboard (`RimStats`)**: a **multi-run monitoring system** with hybrid persistence (Redis + SQLite):

  - **Backend**: FastAPI (Python) serving REST API + WebSocket
  - **Frontend**: React + TypeScript with Plotly charts
  - **Storage**: Redis (hot data) + SQLite (historical data)

- **Shared Protobuf Definitions**: The `.proto` files defining the message schema for communication between the Python agent and RimWorld mod.

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

### Protocol Buffers Schema (`Protos/rimgym.proto`)
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
Run `src/shared/python/src/generate_proto.py` to generate `rimtcp_pb2.py` from the `.proto` file. Only requires `protobuf` package (NOT `grpcio`).

### Build Commands
```powershell
# Full build
dotnet build RimworldMLBridge.sln -c Release

# Verify no native DLLs in output
Get-ChildItem 1.6\Assemblies\*.dll | Where-Object { $_.Name -like "*csharp_ext*" }
# Should return nothing
```

### Harmony Best Practices for RimTCP Mod
- Use `[StaticConstructorOnStartup]` for mod initialization (see `RimTCP`)
- Harmony ID: `"com.jmduea.rimtcp"`
- Always catch exceptions in patch bodies to avoid crashing RimWorld
- Log all important events with `[RimTCP]` prefix for easy filtering

## State Extraction Pattern

**Key RimWorld APIs**:
- `Find.CurrentMap`: Current active map
- `Find.TickManager`: Game time/speed control
- `Find.WorldGrid`: World coordinates
- `Current.Game`: Game session (null in main menu)
- Pawns: `mapPawns.FreeColonistsSpawned`, `AllPawnsSpawned`

## Common Development Tasks

### Adding New Protobuf Messages
1. Edit `Protos/rimgym.proto`
2. Rebuild C# (Grpc.Tools auto-generates C# from `.proto`)
3. Run `src/shared/python/src/generate_proto.py` for Python bindings
4. Update `TcpProtobufServer.ProcessCommands()` to handle new command types

### Configuring Training vs Inference Mode
1. Set `RimTCPMod.TrainingMode = true/false` flag
2. In training mode: Game pauses automatically, only advances on STEP commands
3. In inference mode: Game runs at normal speed, agent polls asynchronously
4. Test both modes: Training for deterministic learning, Inference for real-time robustness

### Debugging Threading Issues
If you see `NullReferenceException` on Unity objects:
- Check if code runs on background thread (bad!)
- Move logic into `TcpProtobufServer.ProcessCommands()` (main thread)
- Use `ConcurrentQueue` to pass data between threads

**Known Issues**:
- If native gRPC DLLs slip into `1.6/Assemblies/`, RimWorld crashes with `BadImageFormatException`
- Solution: Post-build cleanup target in `.csproj` must run successfully

## Code Style Conventions
- Use `[RimTCP]` prefix in all logs for easy filtering
- Wrap Unity API calls in try-catch with graceful degradation
- Check `Current.Game != null` before accessing game state
- Use `?.` null-conditional operator extensively for RimWorld objects
- Comment threading boundaries (main thread vs background thread)

## When You Need to Know More
- **RimWorld modding basics**: Check official docs at https://rimworldwiki.com/wiki/Modding_Tutorials
- **Harmony patching**: https://harmony.pardeike.net/
- **Protocol Buffers**: https://protobuf.dev/
- **Unity threading**: Unity forbids accessing GameObject/Transform from background threads