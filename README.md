# RimGym

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![.NET 8.0](https://img.shields.io/badge/.NET-8.0-512BD4.svg)](https://dotnet.microsoft.com/)
[![RimWorld 1.6](https://img.shields.io/badge/RimWorld-1.6-blue.svg)](https://rimworldgame.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**RimGym** is a comprehensive ecosystem that enables machine learning agents to interact with RimWorld through a high-performance TCP + Protocol Buffers interface. Train reinforcement learning agents to manage colonies, respond to threats, and optimize resource management in real-time.

## 🎯 What is RimGym?

RimGym bridges the gap between the RimWorld game engine and modern reinforcement learning frameworks, providing:

- 🔍 **Real-time Observation**: Extract detailed game state (colonists, map, events, resources) at high frequency
- 🎮 **Action Execution**: Issue commands to pawns (draft, attack, build, prioritize jobs)
- ⚡ **Dual-Mode Operation**: Train agents in deterministic mode or deploy in real-time inference mode
- 🏋️ **Standard Interfaces**: Gymnasium-compatible environment for easy integration with RL frameworks
- 📊 **Live Monitoring**: Real-time dashboard for visualizing agent performance and game state

## 🚀 Quick Start

### Prerequisites

- **RimWorld 1.6** installed via Steam
- **Python 3.11+** for the client
- **.NET 8.0 SDK** (for mod development)
- **Docker** (optional, for containerized testing)

### Installation

1. **Install the RimTCP mod in RimWorld**:

   ```bash
   # Download from Steam Workshop or build from source
   dotnet build src/RimTCP/RimTCP/RimTCP.sln -c Release
   # Copy output to RimWorld mods folder
   ```

2. **Install the Python client**:

   ```bash
   uv sync
   uv run python src/shared/python/src/generate_proto.py
   ```

3. **Start RimWorld and load a save**

4. **Connect your agent**:

   ```python
   import gymnasium as gym
   from gym_env import RimWorldEnv
   
   env = gym.make("RimWorld-v0", host="localhost", port=50051)
   obs, info = env.reset()
   
   for _ in range(1000):
       action = env.action_space.sample()  # Your agent here
       obs, reward, terminated, truncated, info = env.step(action)
   ```

See the [Installation Guide](docs/guides/installation.md) for detailed instructions.

## 📦 Project Components

| Component | Description | Technology |
|-----------|-------------|------------|
| **[RimTCP](src/RimTCP/README.md)** | C# mod that runs inside RimWorld, providing TCP server and game state extraction | C# (.NET Framework 4.8) |
| **[RimGym](src/RimGym/README.md)** | Python client with Gymnasium environment wrapper for RL training | Python 3.11+ |
| **[RimStats](src/RimStats/README.md)** | Real-time dashboard for monitoring agent performance | React + FastAPI |

## 🏗️ Architecture

RimGym uses a **hybrid synchronous/asynchronous architecture** to support both training and inference:

```text
┌─────────────────────────────────────────────────────┐
│                   RimWorld Game                      │
│  ┌────────────────────────────────────────────┐     │
│  │           RimTCP Mod (C#)                 │     │
│  │  ┌──────────────────────────────────┐     │     │
│  │  │  TCP Server (Port 50051)         │     │     │
│  │  │  - State Extraction (Colonists,  │     │     │
│  │  │    Map, Events, Resources)       │     │     │
│  │  │  - Action Execution              │     │     │
│  │  │  - Protobuf Serialization        │     │     │
│  │  └──────────────────────────────────┘     │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
                       ↕ TCP + Protobuf
┌─────────────────────────────────────────────────────┐
│              Python Client (RimGym)                  │
│  ┌────────────────────────────────────────────┐     │
│  │  SpectatorClient (Triple-Threaded)        │     │
│  │  ┌──────────────────────────────────┐     │     │
│  │  │ Listener Thread                  │     │     │
│  │  │ - Async state polling            │     │     │
│  │  │ - Event detection                │     │     │
│  │  └──────────────────────────────────┘     │     │
│  │  ┌──────────────────────────────────┐     │     │
│  │  │ Inference Thread (Executive)     │     │     │
│  │  │ - High-level strategy            │     │     │
│  │  │ - Resource allocation            │     │     │
│  │  └──────────────────────────────────┘     │     │
│  │  ┌──────────────────────────────────┐     │     │
│  │  │ Actor Thread (Reflex)            │     │     │
│  │  │ - Immediate tactical responses   │     │     │
│  │  │ - Combat micro-management        │     │     │
│  │  └──────────────────────────────────┘     │     │
│  └────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────┐     │
│  │  Gymnasium Environment Wrapper            │     │
│  │  - Standard RL interface                  │     │
│  │  - Compatible with SB3, RLlib             │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
                       ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────┐
│               RimStats Dashboard                     │
│  - Real-time metrics visualization                   │
│  - Agent performance monitoring                      │
│  - Event timeline                                    │
└─────────────────────────────────────────────────────┘
```

### Key Features

- **Hybrid Valve System**: Supports both synchronous (training) and asynchronous (inference) modes
- **Triple-Threaded Client**: Separates observation, decision-making, and action execution
- **Hierarchical Policies**: Executive layer for strategy, Reflex layer for tactics
- **Event-Driven Architecture**: Respond to raids, fires, mental breaks, and other game events
- **High Performance**: <50ms observation latency, 1000+ TPS in training mode

See [Architecture Documentation](docs/architecture/README.md) for detailed design.

## 📚 Documentation

- **[Installation Guide](docs/guides/installation.md)** - Detailed setup instructions
- **[Docker Quick Start](docs/docker/QUICKSTART.md)** - 60-second Docker testing setup ⚡
- **[Phase IV Architecture](docs/specs/PHASE_IV_ARCHITECTURE.md)** - Python client design
- **[Phase V Architecture](docs/specs/PHASE_V_ARCHITECTURE.md)** - Full observability design
- **[TCP Protocol](docs/implementation/TCP_PROTOBUF_IMPLEMENTATION.md)** - Protocol details
- **[API Reference](https://jmduea.github.io/RimGym/)** - Full API documentation

## 🧪 Testing

### Unit Tests

```bash
# Python tests
cd src/RimGym
uv run pytest tests/

# C# tests
cd src/RimTCP
dotnet test
```

### Integration Tests

```bash
# Using Docker (recommended)
docker compose up integration

# Manual
# 1. Start RimWorld with RimTCP mod
# 2. Run integration tests
cd src/RimGym
uv run pytest tests/integration/
```

See [Testing Automation](src/RimGym/TESTING_AUTOMATION.md) for details.

## 🐳 Docker Support

Run RimWorld in a containerized environment for automated testing:

```bash
# Quick test
docker compose up test

# Interactive development
docker compose up dev

# Integration tests with health checks
docker compose up integration
```

See [Docker Documentation](docs/docker/README.md) for more options.

## 🤝 Contributing

We welcome contributions! Please see:

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Code Review Standards](CODE_REVIEW.md)
- [Commit Message Format](COMMIT_MESSAGE.md)

## 📋 Roadmap

### ✅ Completed Phases

- **Phase I**: Basic TCP + Protobuf communication
- **Phase II**: Game state observation (colonists, map, events)
- **Phase III**: Action execution and validation
- **Phase IV**: Triple-threaded Python client with hierarchical policies
- **Phase V**: Rich state extraction and production hardening

### 🚧 Phase VI (Planned)

- Advanced policy implementations (resource allocation, base building)
- Multi-agent coordination
- Curriculum learning
- Benchmark scenarios and baselines

See [Changelog](docs/CHANGELOG.md) for version history.

## 🔧 Development

### Building from Source

```bash
# Clone repository
git clone https://github.com/jmduea/RimGym.git
cd RimGym

# Build C# mod
cd src/RimTCP
dotnet restore
dotnet build -c Release

# Install Python client in development mode
cd ../RimGym
uv sync --dev
```

### Project Structure

```text
RimGym/
├── src/
│   ├── RimTCP/          # C# mod for RimWorld
│   ├── RimGym/          # Python client and Gymnasium environment
│   ├── RimStats/        # Dashboard (React + FastAPI)
│   └── shared/          # Shared protobuf definitions
├── tests/               # Integration tests
├── docs/                # Documentation
│   ├── architecture/    # Design documents
│   ├── guides/          # User guides
│   ├── implementation/  # Technical details
│   └── specs/           # Phase specifications
├── scripts/             # Build and deployment scripts
└── docker/              # Docker configuration
```

## 🙏 Acknowledgments

- **RimWorld** by Ludeon Studios
- **Harmony** patching library by Andreas Pardeike
- **Gymnasium** by Farama Foundation
- **Protocol Buffers** by Google

- Portions of the materials used to create this content/mod are trademarks and/or copyrighted works of Ludeon Studios Inc. All rights reserved by Ludeon. This content/mod is not official and is not endorsed by Ludeon.

### Projects that inspired or aided this work

- [**RIMAPI**](https://github.com/IlyaChichkov/RIMAPI)
- [**Rimworld-Together**](https://github.com/RimWorldTogether/RimWorldTogether)

## 📞 Contact

- **GitHub**: [@jmduea](https://github.com/jmduea)
- **Issues**: [GitHub Issues](https://github.com/jmduea/RimGym/issues)
- **Documentation**: [https://jmduea.github.io/RimGym/](https://jmduea.github.io/RimGym/)

---

Built with ❤️ for the RimWorld and ML communities
