# Active Context

## Current Focus (2025-12-10)

**Phase II: RIMAPI Services Integration - "Organ Transplant"**

Porting robust data extraction services from RIMAPI project to replace basic state extraction with high-fidelity DTOs.

## Recent Changes

- ✅ Phase I Complete: TCP+Protobuf server operational
- ✅ Basic state extraction (colonist position, health, needs)
- ✅ STEP command for tick advancement
- ✅ Native DLL exclusion fix (grpc_csharp_ext)
- ✅ Thread-safe command queue implementation
- ✅ Training mode with game pause between steps

## Current Work

- 🔄 Workspace organization and memory bank setup
- 🔄 Creating documentation structure
- 🔄 Planning Services/ DTOs/ Adapters/ architecture

## Next Steps (Priority Order)

1. Complete workspace reorganization
2. Create Services/, DTOs/, Adapters/ directories in RimworldMLBridge/
3. Port ColonistService.cs from RIMAPI (pawn stats, needs, skills)
4. Port MapService.cs from RIMAPI (terrain grid, weather)
5. Extend mlbridge.proto with ColonistState, MapState messages
6. Implement ProtobufAdapter classes for DTO→Protobuf mapping
7. Test serialization performance (<1ms target)

## Active Decisions

- **DEC-001**: Use RIMAPI extraction logic vs. build from scratch → Decided to port RIMAPI for proven robustness
- **DEC-002**: JSON vs Protobuf → Protobuf chosen for performance (<1ms vs ~5-10ms)
- **DEC-003**: gRPC vs raw TCP → Raw TCP due to native DLL incompatibility
- **DEC-004**: Full state vs delta compression → Implement both, toggle by mode
- **DEC-005**: Memory Bank structure → Following memory-bank.instructions.md specification

## Blockers

- None currently

## Questions/Uncertainties

- RIMAPI coupling to HTTP layer - how much refactoring needed?
- Thread-safety patterns for background TCP access to game state
- Optimal chunk size for map delta compression
- Best practices for Protobuf schema evolution

## Recent Learnings

- RimWorld's Mono runtime limitations require careful DLL management
- Length-prefixed framing is simple and efficient for TCP+Protobuf
- Main thread dispatching via ConcurrentQueue works reliably
- Memory bank structure helps maintain context across sessions
