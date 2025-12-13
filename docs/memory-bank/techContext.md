# Tech Context — RimGym

**Last updated:** 2025-12-13

## Languages & Runtimes

- **C# / .NET Framework 4.8** for RimWorld mod runtime (RimTCP).
- **Python 3.11+** for client + Gymnasium env (RimGym).
- **TypeScript/React + FastAPI** for RimStats dashboard.

## Key Libraries / Tools

- **Harmony** patches for hooking RimWorld main loop.
- **Google.Protobuf** for serialization.
- **Gymnasium** for RL environment API.
- **uv** for Python dependency management.
- **Docker / Docker Compose** for containerized workflows.

## Build & Test Commands (Common)

- Python:
  - `uv sync --project src/RimGym`
  - `uv run python src/shared/python/src/generate_proto.py`
  - `uv run pytest src/RimGym/tests/`
- C#:
  - `dotnet build src/RimTCP/RimTCP/RimTCP.sln -c Release`
  - `dotnet test tests/RimTCP.Tests/RimTCP.Tests.csproj -c Release`

## Repo Conventions

- RimWorld/Unity APIs are main-thread-only.
- Avoid native gRPC runtimes.
- Prefix RimTCP logs with `[RimTCP]`.
