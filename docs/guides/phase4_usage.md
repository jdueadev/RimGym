# Phase IV: Python Client Usage Guide

This guide explains how to use the Phase IV Python Triple-Threaded Client for RimTCP.

## Overview

Phase IV implements a sophisticated autonomous agent client with three concurrent threads:

1. **Listener Thread**: Continuously polls RimWorld for state updates and detects events
2. **Inference Thread**: Processes states through strategic policies (ExecutivePolicy)
3. **Actor Thread**: Reacts to urgent events with tactical reflexes (ReflexPolicy)

## Installation

### Basic Installation

```bash
# Clone repository
git clone https://github.com/yourusername/RimGym.git
cd RimGym

# Install core dependencies
uv sync
```

### Training Dependencies

For training RL agents, install additional dependencies:

```bash
uv sync --extra train
```

This installs Stable-Baselines3 and TensorBoard.

## Quick Start

### 1. Start RimWorld Server

Start RimWorld with the ML Bridge mod using Docker:

```bash
# Start RimWorld in test mode
docker-compose up test
```

Or run RimWorld directly with the mod installed.

### 2. Run Spectator Demo

The simplest way to see the client in action:

```bash
# First ensure packages are installed
uv sync

# Run spectator demo
uv run --project src/RimGym python src/RimGym/src/examples/spectator_demo.py --duration 60
```

This will:

- Connect to RimWorld at localhost:50051
- Display colonist status every 2 seconds
- Show detected events in real-time
- Run for 60 seconds

### 3. Use Gymnasium Environment

For RL training, use the Gymnasium wrapper:

```python
from gym_env import RimWorldEnv

# Create environment
env = RimWorldEnv(
    host="localhost",
    port=50051,
    training_mode=True,  # Synchronous mode
    max_episode_steps=1000
)

# Reset environment
obs, info = env.reset()

# Take steps
for _ in range(100):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    
    if terminated or truncated:
        obs, info = env.reset()

env.close()
```

## Architecture

### SpectatorClient

The main client orchestrator managing all three threads:

```python
from client import ClientConfig, SpectatorClient
from policies import ExecutivePolicy, ReflexPolicy

# Create configuration
config = ClientConfig(
    host="localhost",
    port=50051,
    training_mode=False,      # Use async mode
    inference_mode=True,       # Enable strategic policy
    executive_policy=ExecutivePolicy(),
    reflex_policy=ReflexPolicy(),
    poll_interval_ms=100,      # Poll every 100ms
)

# Create and start client
client = SpectatorClient(config)
client.start()

# Wait for ready
client.wait_ready(timeout=30.0)

# Client is now running with all three threads

# Access queues
state = client.state_queue.get_latest()
event = client.event_queue.get(timeout=1.0)
action = client.action_queue.get(timeout=1.0)

# Stop client
client.stop(timeout=5.0)
```

### Thread-Safe Queues

#### StateQueue

```python
# Get latest state (drops older states)
state = client.state_queue.get_latest()

# Get next state in FIFO order
state = client.state_queue.get(timeout=1.0)

# Check if empty
if not client.state_queue.empty():
    state = client.state_queue.get(timeout=0.1)
```

#### EventQueue (Priority-Based)

```python
# Events ordered by priority: CRITICAL > HIGH > MEDIUM > LOW
event = client.event_queue.get(timeout=1.0)

# Event structure
{
    "type": "health_critical",
    "priority": "CRITICAL",
    "colonist_id": "c1",
    "health": 0.15,
    "timestamp": 1234567890.0
}
```

#### ActionQueue

```python
# Get actions from either policy
action = client.action_queue.get(timeout=1.0)

# Action structure
{
    "type": "RESCUE",
    "colonist_id": "c1",
    "target_id": "c2",
    "source": "reflex",  # or "policy"
    "timestamp": 1234567890.0
}
```

### Policies

#### ExecutivePolicy (Strategic)

High-level decision-making for long-term goals:

```python
from policies import ExecutivePolicy

policy = ExecutivePolicy(config={
    "health_critical_threshold": 0.3,
    "enable_health_management": True,
    "enable_task_assignment": True,
})

# Process state
actions = policy.decide(state)

# Get statistics
stats = policy.get_stats()
# {
#     "total_decisions": 100,
#     "actions_generated": 50,
#     "avg_decision_time_ms": 45.2
# }
```

#### ReflexPolicy (Tactical)

Fast reactions to urgent events (<10ms target):

```python
from policies import ReflexPolicy

policy = ReflexPolicy(config={
    "health_critical_threshold": 0.2,
    "enable_auto_rescue": True,
    "enable_danger_avoidance": True,
})

# Process event
actions = policy.decide(event)

# Get statistics
stats = policy.get_stats()
```

### Custom Policies

Create custom policies by subclassing `Policy`:

```python
from policies import Policy

class MyPolicy(Policy):
    def __init__(self, config: dict = None):
        super().__init__(name="MyPolicy", config=config or {})
        # Initialize your policy
    
    def decide(self, data: dict) -> list:
        """Generate actions from state/event."""
        try:
            actions = []
            # Your decision logic here
            self._record_decision(data, actions)
            return actions
        except Exception as e:
            self._record_error(data, str(e))
            return []
```

## Training RL Agents

### Using Stable-Baselines3

```bash
# Train PPO agent
uv run python python/examples/train_agent.py \
    --timesteps 100000 \
    --save-freq 10000 \
    --log-dir ./logs
```

Training script features:

- PPO algorithm with MultiInputPolicy
- Automatic checkpointing every 10k steps
- Evaluation every 5k steps
- TensorBoard logging
- Interrupt handling (saves model on Ctrl+C)

### Custom Training Loop

```python
from gym_env import RimWorldEnv
from stable_baselines3 import PPO

# Create environment
env = RimWorldEnv(
    host="localhost",
    port=50051,
    training_mode=True,
    max_episode_steps=1000
)

# Create PPO model
model = PPO(
    "MultiInputPolicy",
    env,
    verbose=1,
    tensorboard_log="./logs"
)

# Train
model.learn(total_timesteps=100000)

# Save
model.save("rimworld_agent")

env.close()
```

## Running Trained Agents

```bash
# Run inference with trained model
uv run python python/examples/run_inference.py \
    ./logs/best_model/best_model.zip \
    --duration 300
```

This will:

- Load trained model
- Run in asynchronous inference mode
- Display actions taken by agent
- Show statistics every 30 seconds

## Testing

### Unit Tests

```bash
# Run all tests
uv run pytest

# Run specific test module
uv run pytest python/tests/client/test_listener.py

# Run with coverage
uv run pytest --cov=client --cov=policies --cov=gym_env
```

### Integration Tests (Requires Docker)

```bash
# Start RimWorld test server
docker-compose up test

# In another terminal, run integration tests
uv run pytest python/tests/integration/

# Run specific integration test
uv run pytest python/tests/integration/test_full_system.py::TestFullClientIntegration::test_client_connection_and_lifecycle
```

### Performance Benchmarks

```bash
# Run performance benchmarks
uv run pytest python/tests/integration/test_performance.py -v

# Expected results:
# - Listener polling: >10 polls/second
# - Inference latency: <100ms (P95)
# - Reflex latency: <10ms (P95)
# - Observation extraction: <5ms (P95)
# - Reward calculation: <1ms (P95)
```

## Docker Usage

### Development Environment

```bash
# Start development container with mounted code
docker-compose up dev

# Execute commands in container
docker-compose exec dev bash
```

### Running Tests in Docker

```bash
# Start test environment
docker-compose up test

# Run integration tests
docker-compose exec test pytest python/tests/integration/
```

### Building Production Image

```bash
# Build image
docker-compose build build

# Run container
docker-compose up build
```

## Configuration

### ClientConfig Options

```python
config = ClientConfig(
    # Connection
    host="localhost",
    port=50051,
    reconnect_attempts=3,
    reconnect_backoff=2.0,
    
    # Operating modes
    training_mode=False,      # Sync vs async
    inference_mode=True,      # Enable strategic policy
    
    # Policies
    executive_policy=None,    # Strategic policy
    reflex_policy=None,       # Tactical policy
    
    # Performance
    poll_interval_ms=100,     # Listener poll rate
    state_queue_size=100,
    event_queue_size=1000,
    action_queue_size=1000,
)
```

### Operating Modes

#### Training Mode (Synchronous)

- Game pauses between steps
- Agent has full control
- Deterministic for reproducible training
- Use `training_mode=True` in config

#### Inference Mode (Asynchronous)

- Game runs at normal speed
- Agent observes and suggests actions
- Real-time operation
- Use `training_mode=False, inference_mode=True`

## Event Types

The Listener thread detects these events:

1. **health_critical** (CRITICAL priority)
   - Colonist health below threshold
   - Triggers auto-rescue reflex

2. **health_warning** (HIGH priority)
   - Colonist health declining
   - Suggests medical attention

3. **colonist_joined** (MEDIUM priority)
   - New colonist joined colony
   - Opportunity for task assignment

4. **colonist_missing** (HIGH priority)
   - Previously seen colonist disappeared
   - May indicate death or kidnapping

5. **job_changed** (LOW priority)
   - Colonist job changed
   - Useful for activity monitoring

## Performance Considerations

### Latency Targets

- **Reflex Policy**: <10ms per decision (P95)
- **Executive Policy**: <100ms per decision (P95)
- **Observation Extraction**: <5ms (P95)
- **Reward Calculation**: <1ms (P95)

### Optimization Tips

1. **Adjust poll interval**: Balance responsiveness vs CPU usage
2. **Use delta compression**: Only process changed colonists
3. **Batch actions**: Combine multiple actions when possible
4. **Profile policies**: Use `policy.get_stats()` to identify bottlenecks

### Memory Management

- StateQueue keeps only most recent states (max 100)
- EventQueue automatically prioritizes critical events
- ActionQueue processes in FIFO order
- Old actions are dropped if not consumed

## Troubleshooting

### Connection Issues

```python
# Check if server is reachable
from client.connection import ConnectionManager

conn = ConnectionManager(host="localhost", port=50051)
if conn.connect(timeout=5.0):
    print("Server reachable!")
    conn.disconnect()
else:
    print("Server not available")
```

### Performance Issues

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitor queue sizes
print(f"State queue: {client.state_queue.qsize()}")
print(f"Event queue: {client.event_queue.qsize()}")
print(f"Action queue: {client.action_queue.qsize()}")

# Check policy statistics
exec_stats = config.executive_policy.get_stats()
reflex_stats = config.reflex_policy.get_stats()
```

### Docker Issues

```bash
# Check RimWorld logs
docker-compose logs test

# Verify volume setup
docker volume inspect rimworld-data

# Rebuild containers
docker-compose build --no-cache
```

## Advanced Usage

### Multi-Agent Systems

Run multiple agents with different policies:

```python
# Strategic agent
strategic_config = ClientConfig(
    port=50051,
    inference_mode=True,
    executive_policy=ExecutivePolicy(),
    poll_interval_ms=500,  # Slower polling
)
strategic_client = SpectatorClient(strategic_config)

# Reactive agent
reactive_config = ClientConfig(
    port=50051,
    inference_mode=True,
    reflex_policy=ReflexPolicy(),
    poll_interval_ms=50,  # Fast polling
)
reactive_client = SpectatorClient(reactive_config)
```

### Custom Observation Spaces

Modify observation space for specific tasks:

```python
from gym_env.spaces import ObservationSpace
import gymnasium as gym

# Custom extraction
def extract_custom_obs(state: dict) -> dict:
    obs = ObservationSpace.extract_observation(state)
    # Add custom features
    obs["custom"] = calculate_custom_features(state)
    return obs
```

### Custom Reward Functions

Define task-specific rewards:

```python
from gym_env.rewards import RewardCalculator

class CustomRewardCalculator(RewardCalculator):
    def compute_reward(self, state: dict) -> float:
        reward = super().compute_reward(state)
        # Add custom reward components
        reward += self._compute_custom_reward(state)
        return reward
    
    def _compute_custom_reward(self, state: dict) -> float:
        # Your custom logic
        return 0.0
```

## API Reference

See inline documentation in:

- `python/client/` - Client components
- `python/policies/` - Policy implementations
- `python/gym_env/` - Gymnasium environment
- `python/tests/` - Test examples

## Examples

All examples are in `python/examples/`:

1. **spectator_demo.py** - Basic observation without actions
2. **train_agent.py** - Full training pipeline with SB3
3. **run_inference.py** - Run trained agent in inference mode

## Support

For issues and questions:

- GitHub Issues: [repository URL]
- Documentation: `docs/` directory
- Test examples: `python/tests/` directory
