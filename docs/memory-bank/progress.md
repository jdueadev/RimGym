# Progress — RimGym

**Last updated:** 2025-12-13

## What Works

- TCP + Protobuf transport (no native gRPC runtime).
- Length-prefixed framing (4-byte big-endian + protobuf bytes).
- Dual-mode operation (training sync, inference async).
- Main-thread dispatch pattern via Harmony patching.
- Documentation site structure in `docs/` and generated `site/`.
- Python environment management via `uv`.

## In Progress

- No active feature implementation tracked in Memory Bank yet (Memory Bank was empty prior to 2025-12-13).

## Planned / Next Major Work (High Level)

- Phase VI items (per top-level docs):
  - advanced policy implementations
  - multi-agent coordination
  - curriculum learning
  - benchmark scenarios and baselines

## Known Risks / Gotchas

- Any background-thread access to RimWorld APIs can cause intermittent crashes.
- Protobuf schema changes must remain additive; never reuse field numbers.
- Avoid introducing native DLL dependencies into RimTCP assemblies.
