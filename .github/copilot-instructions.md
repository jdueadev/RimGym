# RimGym Monorepo - Copilot Instructions

## What This Repo Contains

- **RimTCP (RimWorld Mod)**: C#/.NET Framework 4.8 mod that exposes a TCP server speaking Protocol Buffers.
- **RimGym (Python)**: Python client + Gymnasium environment that connects to RimTCP for RL training/inference.
- **RimStats (Dashboard)**: Real-time observability (FastAPI backend + React/TS frontend) with Redis + SQLite.
- **Shared Protos**: Single source of truth schema used by both C# and Python.

## Non-Negotiables (Read Before Changing Anything)

### Unity/RimWorld Threading Rule

- RimWorld/Unity APIs are main-thread-only.
- The TCP listener runs on a background thread and must never touch `Find.*`, `Current.Game`, `Pawn`, `Thing`, etc.
- Background thread: network I/O + enqueue/dequeue only.
- Main thread (Harmony patch on `Root.Update()`): execute commands, extract state, validate actions.

If you violate this, you will get intermittent null refs / crashes.

### No Native gRPC Runtime

- RimWorld (Mono) cannot load native gRPC DLLs (e.g., `grpc_csharp_ext`).
- Keep runtime transport as raw TCP + managed protobuf only.
- `Grpc.Tools` is for build-time codegen only.

## Communication & Modes

TCP framing is length-prefixed: 4-byte big-endian length header + protobuf bytes.

Dual operating modes:

- **Training (Synchronous)**: game pauses; advances only on STEP.
- **Inference (Asynchronous)**: game runs; agent polls state (QUERY_STATE) and issues intents.

## Key Paths (Use These, Don’t Guess)

- Protobuf schema: `src/shared/Protos/rimgym.proto`
- Python proto generation: `src/shared/python/src/generate_proto.py`
- RimTCP build output: `src/RimTCP/1.6/Assemblies/`
- RimStats compose file: `src/RimStats/docker-compose.yml`

## Build & Test Commands

### C# (.NET Framework 4.8)

```powershell
dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release
dotnet test tests\RimTCP.Tests\RimTCP.Tests.csproj -c Release

# Verify no native gRPC DLLs slipped in
Get-ChildItem src\RimTCP\1.6\Assemblies\*.dll | Where-Object { $_.Name -like "*csharp_ext*" }
```

### Python (UV)

```powershell
uv sync
uv run python src/shared/python/src/generate_proto.py
uv run pytest src/RimGym/tests/
uv run ruff format src/RimGym/
uv run ruff check src/RimGym/
```

### Docker

```powershell
# RimStats dashboard
docker compose -f src/RimStats/docker-compose.yml up -d

# Repo-level compose (integration)
docker compose up -d
```

## Logging & Safety Conventions

- Prefix RimTCP logs with `[RimTCP]`.
- Always guard game-state reads: check `Current.Game != null` and null-check `Find.CurrentMap`.
- Catch exceptions inside Harmony patches (do not crash the game loop).

## Protobuf Evolution Rules

- Never reuse field numbers.
- Prefer additive changes (new optional fields) over breaking changes.
- Keep message names consistent across C# and Python (schema is the contract).