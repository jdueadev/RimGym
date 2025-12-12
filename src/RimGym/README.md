# RimGym (Python Environment)

**RimGym** is the Python client and Gymnasium environment for the **RimGym** ecosystem. It connects to the **RimTCP** mod to observe the game state and control agents.

## ✨ Features

- **Gymnasium Interface**: Standard RL interface (`env.step()`, `env.reset()`) for compatibility with libraries like Stable Baselines 3, Ray RLLib, etc.
- **Triple-Threaded Client**: `SpectatorClient` architecture with dedicated threads for:
  - **Listener**: Receiving state updates.
  - **Inference**: Running the policy.
  - **Actor**: Sending commands.
- **Type-Safe API**: Fully typed Python classes generated from Protobuf definitions.
- **Hierarchical Policies**: Support for Executive (high-level) and Reflex (low-level) control layers.

## 🚀 Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Recommended)

### Install via UV

```bash
cd src/RimGym
uv sync
```

## 💻 Usage

### Basic Client Example

```python
from client import SpectatorClient
from shared.python.src import rimgym_pb2

# Connect to the game
client = SpectatorClient(host="localhost", port=50051)
client.connect()

# Get state
state = client.get_state()
print(f"Frame: {state.frame_id}")

# Step simulation (Training Mode)
client.step(ticks=60)
```

### Gymnasium Environment (Coming Soon)

```python
import gymnasium as gym
import rimgym

env = gym.make("RimWorld-v0")
obs, info = env.reset()

while True:
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
```

## 🧪 Testing

Run the automated test suite:

```bash
# From src/RimGym
uv run pytest tests/
```

For full integration testing with the game, see the [Testing Automation Guide](../../docs/guides/testing-automation.md).
