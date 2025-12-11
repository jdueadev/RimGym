# RimWorld ML Bridge Architecture

This document provides a comprehensive overview of the RimWorld ML Bridge architecture, consolidating information from the original design documents and implementation evolution.

## Overview

RimWorld ML Bridge is a high-performance TCP + Protocol Buffers communication layer that enables machine learning agents to observe and control RimWorld game state. The architecture supports both synchronous (training) and asynchronous (inference) operation modes.

## System Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│                      Python RL Agent                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Listener   │  │  Inference  │  │   Actor     │            │
│  │  Thread     │  │  Thread     │  │   Thread    │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                    │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐            │
│  │ StateQueue  │  │ EventQueue  │  │ActionQueue  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└────────────────────────────┬───────────────────────────────────┘
                             │ TCP + Protobuf (Port 50051)
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                    RimWorld Mod (C#)                           │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              TcpProtobufServer                           │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────┐    │  │
│  │  │ Listener  │  │ Command   │  │ Response Queue    │    │  │
│  │  │ Thread    │  │ Queue     │  │                   │    │  │
│  │  └───────────┘  └─────┬─────┘  └───────────────────┘    │  │
│  └───────────────────────┼─────────────────────────────────┘  │
│                          │ Main Thread Dispatch                │
│  ┌───────────────────────▼─────────────────────────────────┐  │
│  │                  Harmony Patches                         │  │
│  │   Root_Update_Patch  │  TickManager_DoSingleTick_Patch  │  │
│  └──────────────────────┴──────────────────────────────────┘  │
│                          │                                     │
│  ┌───────────────────────▼─────────────────────────────────┐  │
│  │               Services & Adapters                        │  │
│  │   ColonistService  │  MapService  │  IncidentService    │  │
│  │   ColonistAdapter  │  MapAdapter  │  WorldAdapter       │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

## Communication Protocol

### Protocol Details

- **Transport**: Raw TCP sockets (port 50051)
- **Serialization**: Protocol Buffers (Google.Protobuf)
- **Framing**: 4-byte big-endian length prefix + protobuf payload
- **Max Message Size**: 10 MB

### Message Types

| Message | Direction | Purpose |
|---------|-----------|---------|
| `CommandMessage` | Client → Server | Send commands (STEP, QUERY_STATE, SET_MODE) |
| `StateMessage` | Server → Client | Full game state response |
| `RichStateMessage` | Server → Client | Extended state with map, incidents, world |

### Command Types

| Command | Description |
|---------|-------------|
| `STEP` | Advance game by N ticks (training mode) |
| `QUERY_STATE` | Get current state without advancing |
| `SET_MODE` | Switch between TRAINING and INFERENCE modes |
| `SET_SPEED` | Change game speed (NORMAL, FAST, SUPERFAST, ULTRAFAST) |
| `RESET` | Reset game state (Phase VI - not yet implemented) |
| `EXECUTE_ACTION` | Execute pawn actions (Phase VI - not yet implemented) |

## Dual-Mode Operation (Hybrid Valve)

### Training Mode (Synchronous)

```text
Agent           Server           Game
  │                │               │
  ├──STEP(N)──────►│               │
  │                ├──Run N ticks─►│
  │                │◄──Complete────┤
  │◄──StateMsg─────┤               │
  │                │               │
  [Agent processes, game waits]
```

- Game pauses between steps
- Deterministic, reproducible training
- Agent controls exact tick advancement

### Inference Mode (Asynchronous)

```text
Agent           Server           Game
  │                │               │
  ├──QUERY_STATE──►│               │
  │                ├──Read state──►│ (game running)
  │◄──StateMsg─────┤               │
  │                │               │
  [Agent processes while game continues]
```

- Game runs at normal speed
- Agent queries state without blocking
- Tests real-time performance under latency

## Data Extraction Pipeline

### Phase V: Rich State Architecture

```text
RimWorld Game State
      ↓
Services Layer (ColonistService, MapService, IncidentService)
      ↓
DTOs (Data Transfer Objects)
      ↓
Protobuf Adapters (MapAdapter, IncidentAdapter, WorldAdapter)
      ↓
RichStateMessage (Protobuf)
      ↓
TCP Network
      ↓
Python Client (parsers.py)
      ↓
RichGameState (Typed Python Models)
      ↓
ML Agent
```

### Available State Data

| Category | Data Points |
|----------|-------------|
| Colonists | 21+ fields: health, needs, skills, traits, relationships, job |
| Map | Terrain grid, buildings, items, zones, rooms |
| Incidents | Event history, active threats, storyteller state |
| World | Factions, settlements, caravans, diplomacy |

## Threading Model

### Critical Constraint

RimWorld runs on Unity's single-threaded main loop. **All game API calls must execute on the main thread**.

### Thread Architecture

1. **Background Thread** (TcpProtobufServer)
   - Listens for TCP connections
   - Reads incoming CommandMessages
   - Enqueues to `ConcurrentQueue<CommandMessage>`
   - Sends StateMessages from response queue

2. **Main Thread** (Harmony Patches)
   - `Root_Update_Patch` runs every frame
   - Dequeues commands from queue
   - Processes commands with game API access
   - Enqueues responses for background thread

3. **Python Client Threads**
   - **ListenerThread**: Receives state messages
   - **InferenceThread**: Runs executive policy (strategic decisions)
   - **ActorThread**: Runs reflex policy (tactical reactions)

## Configuration

### Server Configuration (C#)

See `RimworldMLBridge/Constants.cs`:

```csharp
public const int DefaultPort = 50051;
public const int HeartbeatIntervalSeconds = 30;
public const int MaxConnectionErrors = 10;
public const string HarmonyId = "com.jmduea.rimworldmlbridge";
```

### Client Configuration (Python)

See `python/client/config.py`:

```python
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 50051
DEFAULT_TIMEOUT_SECONDS = 5.0
HEARTBEAT_INTERVAL_SECONDS = 30
```

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| State extraction | <5ms | ~3ms (basic), ~10ms (full) |
| Protobuf serialization | <1ms | <1ms |
| Network round-trip | <5ms (localhost) | ~2ms |
| End-to-end latency | <20ms | ~15ms |

## Future Roadmap (Phase VI)

- **RESET Command**: Game reset via save/load cycle
- **EXECUTE_ACTION**: Intent-based pawn control
- **Action Validation**: Server-side validation before execution
- **Failure Signals**: Event notification for failed actions

## Related Documentation

- [Phase V Architecture](../specs/PHASE_V_ARCHITECTURE.md) - Detailed rich state specification
- [TCP Implementation](../implementation/TCP_PROTOBUF_IMPLEMENTATION.md) - Protocol details
- [Python API](../api/python/overview.md) - Client API reference

## Version History

| Version | Changes |
|---------|---------|
| 0.5.0 | Production-quality refactoring, consolidated docs |
| 0.4.0 | Phase V rich state (map, incidents, world) |
| 0.3.0 | Phase IV triple-threaded client |
| 0.2.0 | TCP+Protobuf (replaced gRPC) |
| 0.1.0 | Initial gRPC implementation |
