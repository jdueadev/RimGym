# RimWorld ML Bridge - Project Brief

## Project Name

RimGym (formerly RimWorld ML Bridge / Project Aether)

## Vision

Enable autonomous AI agents to master RimWorld through deep reinforcement learning by bridging Unity/C# game code with Python ML training frameworks.

## Core Requirements

- **REQ-001**: TCP + Protocol Buffers communication bridge (Port 50051) ✅
- **REQ-002**: Thread-safe main thread dispatcher for Unity API calls ✅
- **REQ-003**: Dual-mode operation (Training: synchronous, Inference: asynchronous) ✅
- **REQ-004**: High-fidelity state extraction (<1ms serialization) ✅ (0.003ms achieved)
- **REQ-005**: Intent-based action system with server-side validation ✅

## Success Criteria

- ✅ Agent can observe full game state (colonists, map, incidents, world)
- ✅ Agent can issue commands that execute reliably
- ✅ System handles real-time latency without frame slip
- ✅ Training achieves >1000 TPS (ticks per second)

## Constraints

- RimWorld's Mono runtime cannot load native C# libraries
- Unity single-threaded architecture (all game API calls on main thread)
- .NET Framework 4.8 compatibility required
- RimWorld 1.6+ mod structure compliance

## Current Status

**Version**: 0.5.0 - **Production Ready** 🚀

All major phases complete:

- Phase I: TCP + Protobuf Foundation ✅
- Phase II: RIMAPI Services Integration ✅
- Phase III: Hybrid Valve (Training/Inference modes) ✅
- Phase IV: Triple-Threaded Python Client ✅
- Phase V: Full Game Observability ✅
- Production Hardening (CI/CD, Docs, Packaging) ✅
- Dashboard (RimStats) ✅

## Key Stakeholders

- **ML Researchers**: Simple, reliable Python API with Gymnasium interface
- **RimWorld Modders**: Clean, maintainable C# code that provides performant access to game state.
- **Me (Jon Duea)**: Cause I think this is awesome.
