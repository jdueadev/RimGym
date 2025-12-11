# Phase IV: Python Triple-Threaded Client Architecture

**Version**: 1.0  
**Date**: 2025-12-10  
**Status**: Design Phase  
**Author**: AI Agent + User

---

## Table of Contents

1. [Overview](#overview)
2. [Design Goals](#design-goals)
3. [System Architecture](#system-architecture)
4. [Thread Architecture](#thread-architecture)
5. [Data Flow](#data-flow)
6. [Policy Hierarchy](#policy-hierarchy)
7. [Event System](#event-system)
8. [Class Diagram](#class-diagram)
9. [API Interfaces](#api-interfaces)
10. [Implementation Plan](#implementation-plan)

---

## Overview

Phase IV implements a **triple-threaded Python client** that enables autonomous AI agents to observe and interact with RimWorld in real-time. The architecture supports both **training** (synchronous, deterministic) and **inference** (asynchronous, real-time) modes.

### Key Components

- **SpectatorClient**: Main orchestrator managing all threads
- **Listener Thread**: Async state polling and event detection
- **Inference Thread**: High-level policy decisions (Executive)
- **Actor Thread**: Immediate tactical responses (Reflex)
- **Gymnasium Wrapper**: Standard RL environment interface

### Success Criteria

- ✅ Handle <50ms observation latency in inference mode
- ✅ Support 1000+ TPS (ticks per second) in training mode
- ✅ Zero-latency reflex responses (<10ms decision time)
- ✅ Graceful handling of game pauses, speed changes, and disconnects
- ✅ Compatible with standard RL frameworks (Stable-Baselines3, Ray RLlib)

---

## Design Goals

### 1. Real-Time Performance

- **Training Mode**: Deterministic, lock-step with game ticks
- **Inference Mode**: Low-latency observation/action pipeline
- **Reflex Layer**: Sub-frame tactical responses

### 2. Robustness

- Connection retry with exponential backoff
- Graceful degradation when game pauses
- Thread-safe state sharing
- Clean shutdown handling

### 3. Extensibility

- Pluggable policy modules (Executive/Reflex)
- Custom event handlers
- Configurable observation/action spaces
- Easy integration with RL libraries

### 4. Debuggability

- Comprehensive logging per thread
- State replay capability
- Performance metrics collection
- Visual debugging tools

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SpectatorClient                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Connection Manager                      │  │
│  │  - TCP Connection Pool                                     │  │
│  │  - Reconnection Logic                                      │  │
│  │  - Health Monitoring                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Listener   │  │  Inference   │  │    Actor     │         │
│  │    Thread    │  │    Thread    │  │    Thread    │         │
│  │              │  │              │  │              │         │
│  │  Poll State  │  │  Executive   │  │   Reflex     │         │
│  │  Detect      │  │  Policy      │  │   Policy     │         │
│  │  Events      │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Shared State & Event Queues             │       │
│  │  - State Queue (Listener → Inference)                │       │
│  │  - Event Queue (Listener → Actor)                    │       │
│  │  - Action Queue (Inference/Actor → RimWorld)         │       │
│  │  - Metrics Queue (All → Logger)                      │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                           ▲  │
                           │  ▼
                  ┌────────────────────┐
                  │   RimWorld Server  │
                  │   (TCP + Protobuf) │
                  └────────────────────┘
```

---

## Thread Architecture

### Listener Thread

**Purpose**: Asynchronously poll game state and detect events.

**Responsibilities**:

- Poll QUERY_STATE at configured intervals (default: 100ms inference, tick-locked training)
- Detect events from state changes (raids, fires, deaths, job completions)
- Populate state queue for Inference thread
- Populate event queue for Actor thread (urgent events only)
- Track connection health and trigger reconnects

**State Machine**:

```
┌─────────────┐
│ CONNECTING  │──Success──▶ POLLING ◀──┐
└─────────────┘               │         │
       ▲                      │         │
       │                  State Rx    Retry
       │                      │         │
    Retry                     ▼         │
       │                  ┌──────────────┴──┐
       └──────────────────│  DISCONNECTED   │
                          └─────────────────┘
```

**Configuration**:

```python
class ListenerConfig:
    poll_interval_ms: int = 100  # Inference mode
    training_mode: bool = False   # Lock to ticks if True
    reconnect_attempts: int = 10
    reconnect_backoff_ms: int = 1000
    health_check_interval_ms: int = 5000
```

### Inference Thread

**Purpose**: High-level strategic decision-making (Executive policy).

**Responsibilities**:

- Consume latest state from state queue
- Run Executive policy (neural network or rule-based)
- Generate high-level actions (assign jobs, manage priorities)
- Queue actions for execution
- Update long-term strategy metrics

**Processing Loop**:

```python
while running:
    state = state_queue.get(timeout=1.0)  # Blocking
    
    # Executive policy inference
    action = executive_policy.decide(state)
    
    # Queue for execution
    action_queue.put(action)
    
    # Update metrics
    metrics_queue.put(inference_metrics)
```

**Latency Budget**: 10-100ms per decision (can be slower than reflex)

### Actor Thread

**Purpose**: Immediate tactical responses (Reflex policy).

**Responsibilities**:

- Monitor event queue for urgent events
- Run Reflex policy (fast, heuristic-based)
- Generate immediate tactical actions (dodge, flee, fight)
- Interrupt/override Executive decisions when needed
- Maintain low-latency response (<10ms)

**Event Priorities**:

```python
class EventPriority(Enum):
    CRITICAL = 0   # Under attack, fire spreading
    HIGH = 1       # Raid starting, mental break
    MEDIUM = 2     # Job completion, item hauled
    LOW = 3        # Mood change, need decrease
```

**Processing Loop**:

```python
while running:
    event = event_queue.get(timeout=0.01)  # Non-blocking, 10ms
    
    if event.priority <= EventPriority.HIGH:
        # Reflex policy (fast heuristics)
        action = reflex_policy.react(event)
        
        # Priority insert into action queue
        action_queue.put_priority(action)
```

**Latency Budget**: <10ms per reaction

---

## Data Flow

### State Flow (Listener → Inference)

```
RimWorld Server
      │
      │ QUERY_STATE every 100ms
      ▼
  Listener Thread
      │
      │ Deserialize Protobuf
      │ Extract observations
      ▼
  State Queue (max size: 10)
      │
      │ get() - blocking
      ▼
 Inference Thread
      │
      │ Executive policy
      ▼
  Action Queue
```

### Event Flow (Listener → Actor)

```
Listener Thread
      │
      │ Detect state changes
      │ (health drop, raid start)
      ▼
Event Detection
      │
      │ Classify priority
      ▼
  Event Queue (max size: 100)
      │
      │ get() - non-blocking
      ▼
   Actor Thread
      │
      │ Reflex policy
      ▼
  Action Queue (priority insert)
```

### Action Flow (Inference/Actor → RimWorld)

```
Action Queue
      │
      │ Merge Inference + Reflex actions
      │ Handle conflicts (Reflex overrides)
      ▼
Action Executor
      │
      │ Serialize to Protobuf
      │ EXECUTE_ACTION command
      ▼
RimWorld Server
      │
      │ Validate & execute
      ▼
    Success/Failure feedback
```

---

## Policy Hierarchy

### Executive Policy (Inference Thread)

**Role**: Long-term strategic planning.

**Input**: Full game state observation.

**Output**: High-level actions (job assignments, priorities).

**Examples**:

- Assign colonist to mining task
- Set research priority
- Plan base expansion
- Manage stockpile priorities

**Implementation Options**:

1. **Neural Network**: PPO/A3C trained on long episodes
2. **Monte Carlo Tree Search**: Planning with game simulation
3. **Rule-Based**: Hand-crafted strategy rules
4. **Hybrid**: NN for learning + rules for safety

### Reflex Policy (Actor Thread)

**Role**: Immediate tactical responses.

**Input**: Urgent events (attacks, fires, breaks).

**Output**: Fast tactical actions (flee, fight, extinguish).

**Examples**:

- Dodge incoming projectile
- Flee from predator
- Extinguish fire immediately
- Stop mental break violence

**Implementation Options**:

1. **Heuristic Rules**: Fast, deterministic responses
2. **Lightweight NN**: Small network (<1ms inference)
3. **Behavior Trees**: Structured reactive logic
4. **Hybrid**: Rules for common cases + NN for complex

### Policy Coordination

**Conflict Resolution**:

```python
def resolve_conflict(executive_action, reflex_action):
    """Reflex overrides Executive for same colonist."""
    if reflex_action.colonist_id == executive_action.colonist_id:
        return reflex_action  # Override
    else:
        return [executive_action, reflex_action]  # Execute both
```

**Shared Context**:

- Both policies access same observation
- Reflex can read Executive's plan
- Executive learns from Reflex overrides

---

## Event System

### Event Detection

**Method**: State diffing between consecutive observations.

**Detectable Events**:

| Event Type | Detection Method | Priority |
|------------|------------------|----------|
| Colonist attacked | Health decrease + attacker nearby | CRITICAL |
| Fire spreading | Fire cell count increase | CRITICAL |
| Raid started | Enemy pawns appeared | HIGH |
| Mental break | Mental state changed | HIGH |
| Job completed | Job state → None | MEDIUM |
| Item hauled | Item position changed | MEDIUM |
| Mood changed | Mood delta > threshold | LOW |
| Need critical | Food/Rest < 0.1 | MEDIUM |

**Implementation**:

```python
class EventDetector:
    def __init__(self):
        self.prev_state = None
    
    def detect(self, current_state):
        """Compare current vs previous state, emit events."""
        events = []
        
        if self.prev_state is None:
            self.prev_state = current_state
            return events
        
        # Colonist health changes
        for colonist in current_state.colonists:
            prev = self.prev_state.get_colonist(colonist.id)
            if prev and colonist.health < prev.health - 0.1:
                events.append(Event(
                    type=EventType.COLONIST_DAMAGED,
                    priority=EventPriority.CRITICAL,
                    colonist_id=colonist.id,
                    damage=prev.health - colonist.health
                ))
        
        # Fire detection
        # ... more event types
        
        self.prev_state = current_state
        return events
```

### Event Structure

```python
@dataclass
class Event:
    type: EventType
    priority: EventPriority
    timestamp: float
    colonist_id: Optional[int] = None
    position: Optional[Tuple[int, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## Class Diagram

```python
# Main Client
class SpectatorClient:
    """Orchestrates all threads and manages connection."""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.connection = None
        self.listener = None
        self.inference = None
        self.actor = None
        self.state_queue = queue.Queue(maxsize=10)
        self.event_queue = queue.PriorityQueue(maxsize=100)
        self.action_queue = queue.Queue(maxsize=100)
        self.metrics_queue = queue.Queue()
    
    def start(self) -> None:
        """Start all threads."""
    
    def stop(self) -> None:
        """Gracefully shutdown all threads."""
    
    def wait_ready(self, timeout: float = 30.0) -> bool:
        """Wait for connection to be ready."""

# Connection Management
class ConnectionManager:
    """Manages TCP connection with reconnection logic."""
    
    def connect(self, host: str, port: int) -> bool:
    def disconnect(self) -> None:
    def send_command(self, cmd: CommandMessage) -> StateMessage:
    def is_healthy(self) -> bool:
    def reconnect(self) -> bool:

# Listener Thread
class ListenerThread(threading.Thread):
    """Async state polling and event detection."""
    
    def __init__(self, connection, state_queue, event_queue, config):
        self.connection = connection
        self.state_queue = state_queue
        self.event_queue = event_queue
        self.config = config
        self.event_detector = EventDetector()
    
    def run(self) -> None:
        """Main polling loop."""
    
    def _poll_state(self) -> Optional[StateMessage]:
        """Query state from RimWorld."""
    
    def _detect_events(self, state: StateMessage) -> List[Event]:
        """Detect events from state changes."""

# Inference Thread
class InferenceThread(threading.Thread):
    """Executive policy for strategic decisions."""
    
    def __init__(self, state_queue, action_queue, policy):
        self.state_queue = state_queue
        self.action_queue = action_queue
        self.policy = policy  # Pluggable
    
    def run(self) -> None:
        """Main inference loop."""
    
    def _decide(self, state: StateMessage) -> Action:
        """Run policy and generate action."""

# Actor Thread
class ActorThread(threading.Thread):
    """Reflex policy for tactical responses."""
    
    def __init__(self, event_queue, action_queue, policy):
        self.event_queue = event_queue
        self.action_queue = action_queue
        self.policy = policy  # Pluggable
    
    def run(self) -> None:
        """Main reaction loop."""
    
    def _react(self, event: Event) -> Optional[Action]:
        """Generate immediate tactical action."""

# Policies (Abstract Base)
class Policy(ABC):
    @abstractmethod
    def decide(self, observation) -> Action:
        """Generate action from observation."""

class ExecutivePolicy(Policy):
    """High-level strategic policy."""

class ReflexPolicy(Policy):
    """Low-latency tactical policy."""

# Gymnasium Environment Wrapper
class RimWorldEnv(gymnasium.Env):
    """Standard Gymnasium interface for RL training."""
    
    def __init__(self, config: ClientConfig):
        self.client = SpectatorClient(config)
        self.observation_space = ...
        self.action_space = ...
    
    def reset(self) -> Tuple[np.ndarray, dict]:
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
    def close(self) -> None:
```

---

## API Interfaces

### SpectatorClient API

```python
# Initialize
client = SpectatorClient(ClientConfig(
    host="localhost",
    port=50051,
    training_mode=False,
    executive_policy=MyExecutivePolicy(),
    reflex_policy=MyReflexPolicy()
))

# Start threads
client.start()
client.wait_ready(timeout=30.0)

# Get current state (latest from state queue)
state = client.get_state(timeout=1.0)

# Send action manually
client.send_action(Action(
    type=ActionType.ASSIGN_JOB,
    colonist_id=42,
    job=JobType.MINE
))

# Get metrics
metrics = client.get_metrics()

# Shutdown
client.stop()
```

### Gymnasium API

```python
import gymnasium as gym
from rimworld_ml_bridge import RimWorldEnv

# Create environment
env = gym.make("RimWorld-v0", config=ClientConfig(...))

# Standard RL loop
obs, info = env.reset()
done = False

while not done:
    action = policy.predict(obs)
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated

env.close()
```

---

## Implementation Plan

### Phase IV.1: Core Infrastructure (Week 1)

**Subtasks**:

1. ConnectionManager with reconnection logic
2. SpectatorClient orchestration
3. Thread-safe queue implementations
4. Basic logging and metrics

**Deliverables**:

- `connection.py`: TCP connection management
- `client.py`: SpectatorClient main class
- `queues.py`: Shared state/event/action queues
- Unit tests for connection retry

### Phase IV.2: Listener Thread (Week 1-2)

**Subtasks**:

1. Implement polling loop
2. State deserialization
3. Event detection system
4. Health monitoring

**Deliverables**:

- `listener.py`: ListenerThread implementation
- `events.py`: Event detection and classification
- Integration tests with mock RimWorld server

### Phase IV.3: Inference Thread (Week 2)

**Subtasks**:

1. Inference loop implementation
2. Abstract Policy interface
3. Simple rule-based Executive policy
4. Action generation and queuing

**Deliverables**:

- `inference.py`: InferenceThread implementation
- `policies/executive.py`: Base executive policy
- `policies/rules.py`: Simple rule-based policy
- Unit tests for policy execution

### Phase IV.4: Actor Thread (Week 2-3)

**Subtasks**:

1. Actor loop implementation
2. Priority-based event handling
3. Simple rule-based Reflex policy
4. Conflict resolution with Executive

**Deliverables**:

- `actor.py`: ActorThread implementation
- `policies/reflex.py`: Base reflex policy
- `policies/heuristics.py`: Fast heuristic policy
- Integration tests for event handling

### Phase IV.5: Gymnasium Wrapper (Week 3)

**Subtasks**:

1. Observation space definition
2. Action space definition
3. Reward function design
4. Episode management (reset/step/close)

**Deliverables**:

- `gym_env.py`: RimWorldEnv implementation
- `spaces.py`: Custom observation/action spaces
- `rewards.py`: Reward function implementations
- Example training script with Stable-Baselines3

### Phase IV.6: Integration & Testing (Week 3-4)

**Subtasks**:

1. End-to-end testing with RimWorld
2. Performance benchmarking
3. Stress testing (long episodes, disconnects)
4. Documentation and examples

**Deliverables**:

- `tests/integration/`: Full integration test suite
- `examples/`: Example scripts (training, inference)
- Performance report
- Updated documentation

---

## Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Observation Latency | <50ms | State query roundtrip |
| Action Latency | <100ms | Action → confirmation |
| Reflex Response Time | <10ms | Event → action decision |
| Training Throughput | >1000 TPS | Steps per second |
| Inference Throughput | >100 FPS | Frames per second |
| Memory Usage | <500MB | Process RSS |
| Connection Recovery | <5s | Disconnect → reconnect |

---

## Risk Mitigation

### Risk: Network Latency Spikes

**Mitigation**:

- Velocity-based position extrapolation
- Predictive state estimation
- Action buffering and batching

### Risk: Game Pause/Speed Changes

**Mitigation**:

- Auto-detect mode switches
- Graceful thread synchronization
- Separate training/inference configs

### Risk: Thread Deadlocks

**Mitigation**:

- Timeout on all queue operations
- No nested locks
- Thread health monitoring

### Risk: Policy Bugs

**Mitigation**:

- Extensive unit tests
- Safe fallback policies
- Action validation before execution

---

## Future Enhancements

### Phase IV.7: Advanced Features (Post-MVP)

- **Multi-agent coordination**: Support multiple colonists with different policies
- **Hierarchical RL**: Learn Executive policy from demonstrations
- **Intrinsic motivation**: Curiosity-driven exploration
- **Transfer learning**: Pre-train on simpler scenarios
- **Visual observations**: Add screenshot/minimap support
- **Distributed training**: Multi-process environment parallelization

---

## Appendix A: Configuration Schema

```python
@dataclass
class ClientConfig:
    # Connection
    host: str = "localhost"
    port: int = 50051
    connect_timeout: float = 10.0
    reconnect_attempts: int = 10
    reconnect_backoff: float = 1.0
    
    # Operating Mode
    training_mode: bool = False
    inference_mode: bool = True
    
    # Listener
    poll_interval_ms: int = 100
    max_state_queue_size: int = 10
    health_check_interval_ms: int = 5000
    
    # Inference
    max_inference_latency_ms: int = 100
    executive_policy: Optional[Policy] = None
    
    # Actor
    max_reflex_latency_ms: int = 10
    max_event_queue_size: int = 100
    reflex_policy: Optional[Policy] = None
    
    # Logging
    log_level: str = "INFO"
    metrics_enabled: bool = True
    metrics_interval_ms: int = 1000
```

---

## Appendix B: Testing Strategy

### Unit Tests

- Connection manager retry logic
- Event detection accuracy
- Policy decision consistency
- Queue thread-safety

### Integration Tests

- Full client lifecycle (start → run → stop)
- Mode switching (training ↔ inference)
- Reconnection after disconnect
- Long-running stability (1hr+)

### Performance Tests

- Latency benchmarks
- Throughput stress tests
- Memory leak detection
- CPU profiling

### End-to-End Tests

- Real RimWorld game scenarios
- Multi-colonist coordination
- Raid response
- Base building

---

**Next Steps**: Review architecture, implement Phase IV.1 (Core Infrastructure).
