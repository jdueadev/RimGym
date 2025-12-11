# [TASK004] - Phase IV: Python Triple-Threaded Client

**Status:** In Progress  
**Added:** 2025-12-10  
**Updated:** 2025-12-10

## Original Request

Implement Phase IV: Python Triple-Threaded Client for autonomous RL agent interaction with RimWorld.

**Goal**: Enable AI agents to observe game state and take actions in real-time through a robust, low-latency Python client.

## Thought Process

The architecture follows a **separation of concerns** pattern:

1. **Listener Thread**: Dedicated to I/O - polling state without blocking other operations
2. **Inference Thread**: Strategic planning with higher latency budget (10-100ms)
3. **Actor Thread**: Tactical responses requiring sub-10ms reactions

This design enables:

- **Parallel processing**: All threads work concurrently
- **Priority handling**: Critical events get immediate attention
- **Graceful degradation**: If one policy is slow, others continue
- **Testability**: Each thread can be tested independently

Key architectural decisions:

- **Queues over shared state**: Prevents race conditions, enables backpressure
- **Priority queues for events**: Critical events (attacks) bypass normal flow
- **Reflex overrides Executive**: Safety-critical reactions take precedence
- **Pluggable policies**: Easy to swap rule-based ↔ neural network policies

## Implementation Plan

### Phase IV.1: Core Infrastructure ✅ Ready to Start

**Goal**: Connection management and thread orchestration.

**Components**:

1. `ConnectionManager`: TCP connection with reconnection logic
2. `SpectatorClient`: Main orchestrator managing all threads
3. Thread-safe queues with proper sizing
4. Logging and metrics infrastructure

**Files**:

- `python/client/connection.py`
- `python/client/spectator_client.py`
- `python/client/queues.py`
- `python/client/metrics.py`

**Tests**:

- Connection retry with exponential backoff
- Thread lifecycle (start/stop)
- Queue overflow handling
- Graceful shutdown

**Acceptance**:

- Can connect to RimWorld server
- Reconnects after disconnect
- All threads start/stop cleanly
- No deadlocks or race conditions

---

### Phase IV.2: Listener Thread

**Goal**: Async state polling and event detection.

**Components**:

1. Polling loop with configurable interval
2. State deserialization from Protobuf
3. Event detection via state diffing
4. Health monitoring

**Files**:

- `python/client/listener.py`
- `python/client/events.py`
- `python/client/state_diff.py`

**Tests**:

- Polling at correct intervals
- Event detection accuracy
- Queue population
- Health check triggers

**Acceptance**:

- Polls state every 100ms in inference mode
- Detects colonist damage, raids, fires
- Populates state queue for Inference
- Populates event queue for Actor

---

### Phase IV.3: Inference Thread

**Goal**: Strategic policy execution.

**Components**:

1. Inference loop consuming state queue
2. Abstract Policy interface
3. Simple rule-based Executive policy
4. Action generation

**Files**:

- `python/client/inference.py`
- `python/policies/policy.py` (abstract base)
- `python/policies/executive.py`
- `python/policies/rules.py` (simple example)

**Tests**:

- Policy invocation with state
- Action generation
- Queue timeout handling
- Metrics collection

**Acceptance**:

- Consumes states from queue
- Generates valid actions
- Handles policy errors gracefully
- Latency <100ms per decision

---

### Phase IV.4: Actor Thread

**Goal**: Tactical reflex responses.

**Components**:

1. Event monitoring loop
2. Priority-based processing
3. Reflex policy (heuristic-based)
4. Conflict resolution with Executive

**Files**:

- `python/client/actor.py`
- `python/policies/reflex.py`
- `python/policies/heuristics.py`

**Tests**:

- Priority event handling
- Fast decision latency (<10ms)
- Conflict resolution
- Override logic

**Acceptance**:

- Processes high-priority events first
- Generates tactical actions <10ms
- Overrides Executive when needed
- Handles event queue overflow

---

### Phase IV.5: Gymnasium Wrapper

**Goal**: Standard RL environment interface.

**Components**:

1. Observation space definition
2. Action space definition
3. Reward function
4. Episode management

**Files**:

- `python/gym_env/rimworld_env.py`
- `python/gym_env/spaces.py`
- `python/gym_env/rewards.py`

**Tests**:

- Gymnasium API compliance
- Episode reset/step/close
- Observation/action space validation
- Reward calculation

**Acceptance**:

- Compatible with Stable-Baselines3
- Observation space matches state
- Action space maps to commands
- Rewards computed correctly

---

### Phase IV.6: Integration & Testing

**Goal**: Full system validation.

**Components**:

1. End-to-end integration tests
2. Performance benchmarks
3. Stress tests
4. Documentation

**Files**:

- `python/tests/integration/test_full_client.py`
- `python/examples/train_agent.py`
- `python/examples/run_inference.py`
- `docs/guides/phase4_usage.md`

**Tests**:

- Full lifecycle with RimWorld
- Long-running stability (1hr+)
- Mode switching
- Reconnection scenarios

**Acceptance**:

- All performance targets met
- No memory leaks
- Comprehensive documentation
- Working training example

---

## Progress Tracking

**Overall Status:** In Progress - Phase IV.1 Complete  
**Completion:** 16% (1 of 6 phases)

### Subtasks

| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 4.1 | Core Infrastructure (Connection, Client, Queues) | ✅ Complete | 2025-01-19 | All components implemented, tests passing |
| 4.2 | Listener Thread (Polling, Events) | Not Started | 2025-01-19 | Depends on 4.1 |
| 4.3 | Inference Thread (Executive Policy) | Not Started | 2025-01-19 | Depends on 4.1, 4.2 |
| 4.4 | Actor Thread (Reflex Policy) | Not Started | 2025-01-19 | Depends on 4.1, 4.2 |
| 4.5 | Gymnasium Wrapper | Not Started | 2025-01-19 | Depends on 4.1-4.4 |
| 4.6 | Integration & Testing | Not Started | 2025-01-19 | Depends on 4.1-4.5 |

## Progress Log

### 2025-01-19

**Phase IV.1 COMPLETE** - Core Infrastructure implemented and tested

**Implemented Components:**
1. **ConnectionManager** (python/client/connection.py - 270 lines)
   - TCP socket connection management
   - Exponential backoff reconnection: 1s→2s→4s...→30s (10 attempts)
   - Length-prefixed protobuf framing (4-byte big-endian header)
   - Thread-safe operations with `threading.Lock`
   - Health monitoring and context manager support

2. **SpectatorClient** (python/client/spectator_client.py - 280 lines)
   - Main orchestrator for all threads
   - Lifecycle management (INITIALIZED→CONNECTING→RUNNING→STOPPED)
   - ClientConfig for flexible configuration
   - Metrics thread for performance monitoring
   - Queue wiring and synchronization
   - Context manager support

3. **Queue System** (python/client/queues.py - 265 lines)
   - **StateQueue**: FIFO with maxsize=10, auto-drops oldest, `get_latest()`
   - **EventQueue**: Priority-based (CRITICAL/HIGH/MEDIUM/LOW), maxsize=100
   - **ActionQueue**: FIFO, maxsize=100
   - All queues track dropped items, thread-safe

4. **Metrics** (python/client/metrics.py - 270 lines)
   - MetricsCollector with sliding window statistics
   - PerformanceMetrics dataclass for snapshots
   - Tracks: Throughput, latencies, queue health, connection status
   - Counters and event tracking

**Tests & Validation:**
- Unit tests created: test_connection.py (180 lines), test_queues.py (250 lines)
- Component test: test_phase_iv1.py (155 lines)
- **All 7 tests passing**: Imports, queues, connection, metrics, config, client
- Dependencies synced: protobuf==6.33.2, gymnasium==1.2.2, pytest==9.0.2
- Protobuf Python bindings generated successfully

**Updated Files:**
- pyproject.toml: version→0.3.0, Python≥3.11, gymnasium added
- python/client/__init__.py: Exports all core classes

**Next Steps:**
- Phase IV.2: Implement Listener thread (state polling, event detection)

### 2025-12-10

- Created comprehensive architecture document (PHASE_IV_ARCHITECTURE.md)
- Defined triple-threaded design (Listener/Inference/Actor)
- Specified Executive/Reflex policy hierarchy
- Designed event system and priority handling
- Created class diagram and API interfaces
- Defined performance targets and success criteria
