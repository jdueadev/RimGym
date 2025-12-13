# Active Context — RimGym

**Status:** Phase VI feature work in progress
**Last updated:** 2025-12-13

## Current Focus

- Phase VI: implement Gym-compatible RESET using “load known save”.
- Wire Python Gym env RESET/STEP to real TCP+Protobuf commands.

## Recent Context

- Latest commit on this branch: `98ec09e` — “documentation refresh”.

## Immediate Next Steps

- Verify RESET in a live RimWorld session (load a known save via `RIMTCP_RESET_SAVE`).
- If stable, implement `EXECUTE_ACTION` and wire Gym `step()` to use it (rather than action_queue only).
- Keep Memory Bank current (TASK002 created for RESET implementation).

## Known Constraints to Keep Top-of-Mind

- Main-thread-only RimWorld APIs (network thread must queue only).
- TCP length-prefix framing + managed protobuf only.
