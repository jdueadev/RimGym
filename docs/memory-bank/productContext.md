# Product Context — RimGym

**Last updated:** 2025-12-13

## Why This Project Exists

RimWorld is a rich, partially observable, event-driven simulation with long-horizon planning challenges. RimGym exists to make RimWorld **programmable** for machine learning research and engineering by exposing game state and accepting agent intents through a stable, high-performance interface.

## Problems It Solves

- **No standard RL interface** to RimWorld: RimGym provides a Gymnasium-compatible environment.
- **Game/runtime constraints**: RimWorld runs on a main-thread Unity loop and can’t load native gRPC; RimGym uses TCP + managed protobuf with correct threading.
- **Observability gap**: RimStats provides live monitoring of agent behavior and state.

## Target Users

- ML/RL practitioners who want to train or evaluate agents in RimWorld.
- Engineers iterating on agents and environments who need deterministic stepping and reliable state.
- Contributors extending state extraction, actions, and observability.

## How It Should Work (User Experience)

- Developer can:
  - Build and install the RimTCP mod.
  - Generate Python protobuf bindings.
  - Run a Gymnasium env that can reset, step, and query state.
- Training mode supports deterministic step-driven advancement.
- Inference mode supports real-time polling and command issuance without stalling the game.
- Errors are actionable: logs indicate whether failures were networking, parsing, or game-side validation.

## Success Signals

- End-to-end loop runs for extended sessions without crashes.
- State payloads and commands remain backward compatible (additive protobuf evolution).
- The client can maintain low latency on localhost and degrade gracefully under load.
