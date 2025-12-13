# [TASK002] - Implement RESET (Load Known Save)

**Status:** In Progress  
**Added:** 2025-12-13  
**Updated:** 2025-12-13

## Original Request

Preferred reset strategy: load known save. Start implementation.

## Thought Process

RESET is required for a Gymnasium-compatible RL loop. RimWorld APIs are main-thread-only, so RESET must be initiated and tracked from the Unity thread (Harmony `Root.Update`/server command processing). A save-load cycle can take longer than typical request/response windows, so the system needs a clear “reset in progress” signal so clients can poll until ready.

## Implementation Plan

- Extend protobuf contract to include `CommandMessage.reset_save_name`.
- Implement server-side RESET handler to queue a save load on the main thread and expose `reset_in_progress` in `RichStateMessage`.
- Wire Python Gym `env.reset()` to send RESET and poll until completion.
- Regenerate Python protos and update unit tests.
- Validate in a live RimWorld session.

## Progress Tracking

**Overall Status:** In Progress - 80%

### Subtasks

| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 2.1 | Add `reset_save_name` to proto | Complete | 2025-12-13 | Additive schema change |
| 2.2 | Add reset progress fields to `RichStateMessage` | Complete | 2025-12-13 | `reset_in_progress`, `reset_save_name` |
| 2.3 | Implement RimTCP RESET (save-load cycle) | Complete | 2025-12-13 | Uses `LongEventHandler.QueueLongEvent` + reflection |
| 2.4 | Wire Gym `reset()` to send RESET + wait | Complete | 2025-12-13 | Polls `QUERY_STATE` until ready |
| 2.5 | Regenerate Python protos + update unit tests | Complete | 2025-12-13 | `tests/gym_env` updated |
| 2.6 | Live in-game verification | Not Started | 2025-12-13 | Needs RimWorld runtime check |

## Progress Log

### 2025-12-13

- Extended [src/shared/Protos/rimgym.proto](src/shared/Protos/rimgym.proto) with RESET save targeting and reset progress fields.
- Implemented RESET tracking + long-event save load in [src/RimTCP/RimTCP/TcpProtobufServer.cs](src/RimTCP/RimTCP/TcpProtobufServer.cs).
- Wired Gym env reset/step in [src/RimGym/src/gym_env/rimworld_env.py](src/RimGym/src/gym_env/rimworld_env.py) and updated mocks in [src/RimGym/tests/gym_env/test_gymnasium.py](src/RimGym/tests/gym_env/test_gymnasium.py).
- Regenerated Python protobuf bindings via `src/shared/python/src/generate_proto.py`.
- Next: verify reset behavior in a real RimWorld session and document the operational workflow (env var `RIMTCP_RESET_SAVE`).
