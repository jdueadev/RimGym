# System Patterns — RimGym

**Last updated:** 2025-12-13

## High-Level Architecture Pattern

A three-part system:

1. **RimTCP (in RimWorld)** exposes a TCP server.
2. **Python client + Gymnasium env** connects via TCP and exchanges protobuf messages.
3. **RimStats** ingests/visualizes state and metrics (observability).

## Contract-First Pattern (Shared Protobuf)

- `.proto` is the contract shared by both C# and Python.
- Evolution rules:
  - Never reuse field numbers.
  - Prefer additive changes.

## Transport Pattern (TCP + Protobuf)

- Raw TCP sockets with **length-prefix framing**:
  - 4-byte big-endian message length
  - protobuf payload bytes

## Threading Pattern (Main-Thread Dispatch)

- Background thread:
  - network I/O
  - enqueue/dequeue only
- Main thread (Harmony patch on `Root.Update()`):
  - execute commands
  - read game state
  - build protobuf responses

## Dual-Mode “Hybrid Valve” Pattern

- **Training (sync)**: the simulation advances only when the agent sends STEP.
- **Inference (async)**: the simulation runs; agent periodically queries state.

## Monorepo Pattern

- `src/RimTCP/` — mod runtime + server
- `src/RimGym/` — python client + gym env
- `src/RimStats/` — dashboard
- `src/shared/` — shared schemas and codegen

## Operational Pattern (Docker + Scripts)

- Docker Compose configurations exist for integration/testing.
- Scripts in `scripts/` manage volume setup and verification.
