# Active Context

## Current Focus (2025-12-10)

### 🚀 Phase IV: Python Triple-Threaded Client - STARTING

**Goal**: Develop autonomous RL agent client that can observe and interact with RimWorld in real-time.

**Status**: Fresh start on main branch after PR #3 merged successfully.

## Recent Changes

- ✅ **PR #3 Merged**: Phases I-III complete and merged to main
- ✅ **Phase I-III**: TCP+Protobuf, RIMAPI Services, Hybrid Valve all operational
- ✅ **Docker CI/CD**: Automated testing infrastructure complete
- ✅ **Branch Cleanup**: feature/phase2-rimapi-services-integration deleted
- ✅ **Working Directory**: Clean, on main branch
- 🎯 **Ready**: Starting Phase IV implementation

## Current Work

### Phase IV Architecture Design

Designing triple-threaded client with:
1. **Listener Thread**: Async state polling, event detection
2. **Inference Thread**: High-level policy (Executive layer)
3. **Actor Thread**: Immediate responses (Reflex layer)

### Immediate Next Steps

1. **Design Phase IV Architecture**
   - Define thread communication patterns (queues, locks)
   - Design Executive/Reflex policy hierarchy
   - Plan interrupt event system
   - Create class structure diagram

2. **Implement SpectatorClient Base**
   - Connection management and reconnection logic
   - Thread lifecycle management
   - State queue and event queue
   - Graceful shutdown handling

3. **Implement Listener Thread**
   - Async state polling loop
   - Event detection from state changes
   - State queue population
   - Performance monitoring

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
