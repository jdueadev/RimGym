# Project Brief — RimGym

**Last updated:** 2025-12-13

## Mission

Build a reliable, high-performance bridge between **RimWorld 1.6** and modern RL tooling so that agents can **observe** and **act** in-game via a stable, typed protocol.

## What This Repo Is

A monorepo containing:

- **RimTCP (RimWorld Mod)**: TCP server + main-thread command execution + game state extraction.
- **RimGym (Python)**: Gymnasium-compatible environment + client(s) connecting to RimTCP.
- **RimStats (Dashboard)**: Observability stack (backend + frontend) for live state/metrics.
- **Shared Protobuf schema**: Single source of truth contract used by both C# and Python.

## Primary Goals

- Provide **typed, versioned** messages for state + commands (Protocol Buffers).
- Support two operating modes:
  - **Training (synchronous)**: game advances only on STEP.
  - **Inference (asynchronous)**: game runs; client polls state and sends intents.
- Maintain a stable **Gymnasium** interface for RL frameworks.
- Keep the system robust inside RimWorld’s constraints (Mono/Unity, main-thread-only APIs).

## Non‑Negotiables / Hard Constraints

- **Unity/RimWorld API access must be main-thread-only.** Background threads may do I/O and queueing only.
- **No native gRPC runtime**: RimWorld/Mono cannot load native gRPC DLLs (e.g., `grpc_csharp_ext`). Transport is raw TCP + managed protobuf.
- **TCP framing** is length-prefixed: 4-byte big-endian length header + protobuf bytes.

## Legal / Disclaimer

Portions of the materials used to create this content/mod are trademarks and/or copyrighted works of Ludeon Studios Inc. All rights reserved by Ludeon. This content/mod is not official and is not endorsed by Ludeon.

## Key Paths (Source of Truth)

- Protobuf schema: `src/shared/Protos/rimgym.proto`
- Python proto generation: `src/shared/python/src/generate_proto.py`
- RimTCP build output: `src/RimTCP/1.6/Assemblies/`
- RimStats compose file: `src/RimStats/docker-compose.yml`

## Out of Scope (for now)

- Native gRPC transport in RimWorld.
- Overly game-specific “one-off” hacks that break determinism or stability.
