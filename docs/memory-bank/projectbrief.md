# RimWorld ML Bridge - Project Brief

## Project Name

RimWorld ML Bridge (Project Aether)

## Vision

Enable autonomous AI agents to master RimWorld through deep reinforcement learning by bridging Unity/C# game code with Python ML training frameworks.

## Core Requirements

- **REQ-001**: TCP + Protocol Buffers communication bridge (Port 50051)
- **REQ-002**: Thread-safe main thread dispatcher for Unity API calls
- **REQ-003**: Dual-mode operation (Training: synchronous, Inference: asynchronous)
- **REQ-004**: High-fidelity state extraction (<1ms serialization)
- **REQ-005**: Intent-based action system with server-side validation

## Success Criteria

- Agent can observe full game state (colonists, map, jobs)
- Agent can issue commands that execute reliably
- System handles real-time latency without frame slip
- Training achieves >1000 TPS (ticks per second)

## Constraints

- RimWorld's Mono runtime cannot load native C++ libraries
- Unity single-threaded architecture (all game API calls on main thread)
- .NET Framework 4.8 compatibility required
- RimWorld 1.6+ mod structure compliance

## Current Phase

Phase II: "Organ Transplant" - Porting RIMAPI services for high-fidelity data extraction

## Key Stakeholders

- **ML Researchers**: Need simple, reliable Python API
- **RimWorld Modders**: Need clean, maintainable C# code
- **Project Lead**: Strategic direction and architecture decisions
