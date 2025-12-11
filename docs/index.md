# RimGym Documentation

Welcome to the **RimGym** documentation! This project enables machine learning agents to interact with RimWorld through a high-performance TCP + Protocol Buffers interface.

## 🎯 What is RimGym?

RimGym is a comprehensive ecosystem that connects AI agents to the RimWorld game, enabling:

- **Real-time Observation**: Extract detailed game state (colonists, map, events) at high frequency
- **Action Execution**: Issue commands to pawns (draft, attack, build, prioritize jobs)
- **Dual-Mode Operation**: Train agents in deterministic mode or deploy in real-time inference mode
- **Standard Interfaces**: Gymnasium-compatible environment for easy integration with RL frameworks

## 🚀 Quick Links

<div class="grid cards" markdown>

- :material-rocket-launch:{ .lg .middle } **Getting Started**

    ---

    Install RimGym and run your first agent

    [:octicons-arrow-right-24: Installation Guide](guides/installation.md)

- :material-book-open-variant:{ .lg .middle } **Architecture**

    ---

    Learn about the system architecture

    [:octicons-arrow-right-24: Architecture Overview](architecture/README.md)

- :material-docker:{ .lg .middle } **Docker Setup**

    ---

    Run RimWorld in a containerized environment

    [:octicons-arrow-right-24: Docker Guide](docker/README.md)

- :material-history:{ .lg .middle } **Changelog**

    ---

    See what's new in the latest version

    [:octicons-arrow-right-24: Changelog](CHANGELOG.md)

</div>

## Project Components

| Component | Description |
|-----------|-------------|
| **RimTCP** | C# mod that runs inside RimWorld, providing TCP server and game state extraction |
| **RimGym** | Python client with Gymnasium environment wrapper for RL training |
| **RimStats** | Real-time dashboard for monitoring agent performance |

## Quick Start

1. Install the RimTCP mod in RimWorld
2. Install the Python client: `pip install rimgym`
3. Start RimWorld and load a save
4. Connect your agent and start training!

See the [Installation Guide](guides/installation.md) for detailed instructions.
