# RimGym Project Overview

## Project Name

RimGym (Code Name: Project Aether)

## Version

0.5.0

## Purpose

RimGym enables **autonomous AI agents to master RimWorld through deep reinforcement learning** by bridging Unity/C# game code with Python ML training frameworks via TCP + Protocol Buffers.

## Architecture

```
Python RL Agent (TCP Client)  ←→  RimWorld Mod (TCP Server)
   Port 50051, Protobuf              Background Thread → Main Thread
```

## Three Main Components

| Component | Path | Language | Purpose |
|-----------|------|----------|---------|
| **RimTCP** | `src/RimTCP/` | C# (.NET 4.8) | RimWorld mod - TCP server, Harmony patches, state extraction |
| **RimGym** | `src/RimGym/` | Python 3.11+ | RL client - Gymnasium env, SpectatorClient, training loop |
| **RimStats** | `src/RimStats/` | FastAPI + React | Dashboard - Redis + SQLite for multi-run monitoring |
| **shared** | `src/shared/` | Proto + Python | Shared protobuf schema and generated code |

## Operating Modes

- **Training Mode (Synchronous)**: Game pauses → Agent thinks → STEP → Game runs N ticks
- **Inference Mode (Asynchronous)**: Game runs freely → Agent queries asynchronously

## Critical Constraints

1. **No Native DLLs**: RimWorld's Mono cannot load grpc_csharp_ext.dll → use raw TCP
2. **Main Thread Only**: All Unity API calls must go through main thread (Root_Update_Patch)
3. **.NET Framework 4.8**: Required for RimWorld compatibility
4. **Harmony ID**: `unknwnentity.rimtcp`

## Performance Targets

- Serialization: <1ms for full state (achieved: 0.003ms per colonist)
- Throughput: >1000 TPS per instance
- Round-trip latency: <100ms
