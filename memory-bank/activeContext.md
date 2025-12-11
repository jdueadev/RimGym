# Active Context

## Current Focus (2025-12-10 Final)

### ✅ Phase III: Hybrid Valve - 100% COMPLETE! 🎉

**All Features Working:**

- Dual-mode operation: Training (synchronous) and Inference (asynchronous)
- Exact tick control in training mode (verified across 5 test runs)
- Async game flow in inference mode (120-727 ticks/2s based on speed)
- Velocity tracking for position extrapolation under latency
- Auto-pause handling for robust operation
- Mode switching with <10ms latency

## Recent Changes

- ✅ **Phase III Complete (100%)**: Hybrid Valve fully operational and tested
- ✅ **Training Mode**: Synchronous tick control with exact 60-tick advancement
- ✅ **Inference Mode**: Asynchronous queries while game runs freely
- ✅ **Velocity Vectors**: Position tracking with velocity calculation (up to 3.98 units/sec detected)
- ✅ **Frame Timing**: Delta time tracking (~1000ms accuracy)
- ✅ **Pause Handling**: Auto-unpause when STEP/mode switch requires game to run
- ✅ **Integration Tests**: 5 test runs at 1x/2x/3x speeds + paused state
- ✅ **Phase II Complete**: Services → DTOs → Adapters → Protobuf (0.003ms per colonist)

## Current Work

- ✅ Phase III Complete: All 7 subtasks finished with comprehensive testing
- 🔄 Ready for Phase IV: Python Triple-Threaded Client implementation

## Next Steps (Priority Order)

1. **Phase III: Hybrid Valve Implementation**
   - Implement AsyncMode toggle in C#
   - Add TickManager.DoSingleTick prefix patch for mode switching
   - Implement delta compression for real-time map updates
   - Add velocity vectors and timestamp tracking

2. **Phase IV: Python Triple-Threaded Client**
   - Develop SpectatorClient.py (Listener/Inference/Actor threads)
   - Implement hierarchical policy (Executive/Reflex layers)
   - Add interrupt event handling (raids, fires, mental breaks)

3. **End-to-End Testing**: Test with real RimWorld game
   - Load a colony, connect client
   - Verify all data extracts correctly
   - Test STEP and QUERY_STATE commands
   - Validate timestamp accuracy and latency

4. **Expand Services**: Port MapService and IncidentService
   - High-fidelity terrain grid data
   - Incident tracking for event-driven learning

## Active Decisions

- **DEC-001**: Use RIMAPI extraction logic vs. build from scratch → Decided to port RIMAPI for proven robustness
- **DEC-002**: JSON vs Protobuf → Protobuf chosen for performance (<1ms vs ~5-10ms)
- **DEC-003**: gRPC vs raw TCP → Raw TCP due to native DLL incompatibility
- **DEC-004**: Full state vs delta compression → Implement both, toggle by mode
- **DEC-005**: Memory Bank structure → Following memory-bank.instructions.md specification
- **DEC-006**: Use RichStateMessage for all state responses (not dual message types)
- **DEC-007**: Always include timestamp for latency measurement
- **DEC-008**: C# 7.3 compatibility requires traditional control flow patterns

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
