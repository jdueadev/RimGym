# Active Context — RimGym

**Status:** Stable baseline; maintenance work
**Last updated:** 2025-12-13

## Current Focus

- Documentation and repo hygiene work on branch `chore/misc-cleanup`.
- No uncommitted local changes at time of update.

## Recent Context

- Latest commit on this branch: `98ec09e` — “documentation refresh”.

## Immediate Next Steps

- Keep Memory Bank current as work proceeds (new features should create/update task entries).
- If starting Phase VI work:
  - confirm requirements for action execution / reset semantics
  - update shared protobuf schema additively
  - validate main-thread dispatch remains intact

## Known Constraints to Keep Top-of-Mind

- Main-thread-only RimWorld APIs (network thread must queue only).
- TCP length-prefix framing + managed protobuf only.
