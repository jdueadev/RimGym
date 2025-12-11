# Active Context

## Current Focus (2025-01-19)

### 🚀 Phase IV.3: Inference Thread - STARTING

**Goal**: Implement strategic policy execution layer for high-level decision-making.

**Status**: Phase IV.1 (Core Infrastructure) and Phase IV.2 (Listener Thread) complete. Moving to Phase IV.3.

## Recent Changes

- ✅ **Phase IV.2 Complete**: Listener Thread implemented with comprehensive testing
  - 392-line implementation with 5 event types
  - 23 tests passing (16 unit tests + 7 performance benchmarks)
  - Performance exceeds targets by orders of magnitude (714x-2,941x faster)
  - Event detection: colonist lifecycle, health monitoring, job tracking
  - Polling throughput: 17 polls/sec (target >10)
  
- ✅ **Phase IV.1 Complete**: Core Infrastructure operational
  - ConnectionManager, SpectatorClient, Queue system, Metrics collector
  - All 7 tests passing
  - Thread lifecycle management working correctly

- ✅ **PR #3 Merged**: Phases I-III complete and merged to main
- ✅ **Phase I-III**: TCP+Protobuf, RIMAPI Services, Hybrid Valve all operational

## Current Work

### Phase IV.3: Inference Thread (Next Phase)

Implementing strategic policy execution layer:

1. **InferenceThread**: Consumes states from queue, runs policy, generates actions
2. **Policy Interface**: Abstract base class for pluggable policies
3. **Executive Policy**: High-level strategic decision-making (10-100ms latency budget)
4. **Action Generation**: Create action commands from policy decisions

### Immediate Next Steps

1. **Implement InferenceThread** (python/client/inference.py)
   - Consume states from StateQueue
   - Invoke policy.decide(state) method
   - Generate actions and queue to ActionQueue
   - Handle policy errors gracefully
   - Collect latency metrics

2. **Define Policy Interface** (python/policies/policy.py)
   - Abstract base class with decide(state) method
   - Input: State dictionary
   - Output: List of actions (or None)
   - Error handling contract

3. **Create Simple Executive Policy** (python/policies/executive.py)
   - Rule-based initial implementation
   - Basic colonist management (e.g., "if health <50%, send to medical bed")
   - Testable logic with clear rules

4. **Comprehensive Testing**
   - Unit tests for InferenceThread (state consumption, action generation)
   - Unit tests for Policy interface and Executive implementation
   - Performance benchmarks (latency <100ms target)
   - Integration tests with Listener thread

5. **Integration with SpectatorClient**
   - Update _start_threads() to instantiate and start InferenceThread
   - Wire state_queue, action_queue, stop_event
   - Add metrics collection

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
