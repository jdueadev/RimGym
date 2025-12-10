# RimWorld ML Bridge

A RimWorld mod that provides a gRPC/Protocol Buffer interface for machine learning agents to interact with the game. This enables training reinforcement learning agents to play RimWorld by exposing game state and accepting commands through a structured, high-performance API.

## 🎯 Project Goal

Enable autonomous AI agents to master RimWorld through deep reinforcement learning. This bridge provides the critical infrastructure to connect the Unity-based game engine with Python-based ML training frameworks.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full technical roadmap and theoretical framework.

## ✨ Features

- **gRPC Server**: High-performance, type-safe communication
- **Protocol Buffers**: Efficient binary serialization for game state
- **Game State API**: Access to pawns, entities, global state (temperature, date, etc.)
- **Command Interface**: Execute game commands (STEP, RESET, QUERY_STATE)
- **Multi-client Support**: Multiple agents can connect simultaneously
- **Harmony Integration**: Non-invasive patching of game logic

## 🏗️ Architecture

```
┌─────────────┐         gRPC/Protobuf        ┌──────────────┐
│   RimWorld  │ ◄──────────────────────────► │ Python Agent │
│  (C# Mod)   │      Port 50051              │  (ML Client) │
└─────────────┘                              └──────────────┘
```

### Protocol Definition

The API is defined in `Protos/mlbridge.proto`:

- **TickMessage**: Game tick notifications
- **StateMessage**: Complete game state (pawns, entities, global data)
- **CommandMessage**: Agent commands (NO_OP, STEP, RESET, EXECUTE_ACTION)
- **Action**: Individual pawn actions (GOTO, ATTACK, BUILD, etc.)

### Current Implementation

**✅ Implemented:**
- gRPC server with 3 RPC methods: `SendTick`, `GetState`, `ExecuteCommand`
- Game state extraction (colonists, health, needs, jobs)
- Python client with structured message types
- Build infrastructure for C# and Python

**🚧 Future Enhancements:**
- Action execution (currently returns state but doesn't execute actions)
- Map data (terrain, buildings, items)
- Streaming RPCs for real-time updates
- Advanced pawn control (FloatMenu actions, direct job assignment)

## 🚀 Quick Start

### Prerequisites

**For the C# Mod:**
- .NET SDK 4.7.2 or higher
- RimWorld 1.6+ installation
- Set environment variable: `export RIMWORLD_DIR=/path/to/RimWorld`

**For the Python Client:**
- Python 3.8+
- Dependencies: `pip install grpcio grpcio-tools protobuf`

### Building

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jmduea/RimworldMLBridge.git
   cd RimworldMLBridge
   ```

2. **Build the mod:**
   ```bash
   export RIMWORLD_DIR=/path/to/RimWorld
   ./build.sh
   ```

   Or manually:
   ```bash
   # Build C# mod
   cd Source
   dotnet build RimworldMLBridge.csproj -c Release
   
   # Generate Python protobuf files
   cd ../python
   python generate_proto.py
   ```

3. **Install the mod:**
   - Copy the entire project directory to `RimWorld/Mods/RimworldMLBridge/`
   - Or create a symlink: `ln -s $(pwd) $RIMWORLD_DIR/Mods/RimworldMLBridge`

### Running

1. **Start RimWorld** with the MLBridge mod enabled
2. **Load a game** (not just the main menu)
3. **Check the log** for:
   ```
   [MLBridge] gRPC server started successfully!
   [MLBridge] Listening on localhost:50051
   ```
4. **Run the Python test client:**
   ```bash
   cd python
   python test_connection.py
   ```

## 📡 API Usage

### Python Client Example

```python
import grpc
import mlbridge_pb2
import mlbridge_pb2_grpc

# Connect to the game
channel = grpc.insecure_channel('localhost:50051')
stub = mlbridge_pb2_grpc.MLBridgeStub(channel)

# Get game state
state = stub.GetState(mlbridge_pb2.EmptyMessage())
print(f"Frame: {state.frame_id}")
print(f"Colonists: {len(state.entities)}")

for entity in state.entities:
    print(f"  {entity.def_name}: Health={entity.state.health:.1%}")

# Send a command
response = stub.ExecuteCommand(mlbridge_pb2.CommandMessage(
    type=mlbridge_pb2.STEP,
    ticks_to_run=60  # Advance 1 second
))

# Send tick acknowledgment
ack = stub.SendTick(mlbridge_pb2.TickMessage(
    tick_count=1,
    frame_id=state.frame_id
))
```

### Available RPC Methods

#### `GetState(EmptyMessage) → StateMessage`
Returns current game state including:
- Frame ID (tick count)
- Global state (day, year, temperature)
- All colonist pawns with position, health, needs, current job

#### `ExecuteCommand(CommandMessage) → StateMessage`
Execute a command and get resulting state:
- `NO_OP`: No operation
- `STEP`: Advance simulation
- `RESET`: Reset game state
- `QUERY_STATE`: Same as GetState
- `EXECUTE_ACTION`: Execute pawn actions (future)

#### `SendTick(TickMessage) → AckMessage`
Send tick notification, returns acknowledgment.

## 🔧 Development

### Project Structure

```
RimworldMLBridge/
├── About/                      # RimWorld mod metadata
│   └── About.xml
├── Assemblies/                 # Compiled C# DLLs (output)
│   └── RimworldMLBridge.dll
├── Protos/                     # Protocol Buffer definitions
│   └── mlbridge.proto
├── Source/                     # C# source code
│   ├── RimworldMLBridge.cs    # Main mod entry, gRPC server
│   ├── GrpcService.cs         # gRPC service implementation
│   ├── TickPatch.cs           # Harmony patches
│   └── RimworldMLBridge.csproj
├── python/                     # Python client
│   ├── test_connection.py     # Example client
│   ├── generate_proto.py      # Proto file generator
│   ├── mlbridge_pb2.py        # Generated (excluded from git)
│   └── mlbridge_pb2_grpc.py   # Generated (excluded from git)
├── build.sh                    # Build script
├── pyproject.toml             # Python package configuration
└── README.md                   # This file
```

### Building from Source

**C# Dependencies (auto-installed via NuGet):**
- `Grpc.Core` 2.46.6
- `Google.Protobuf` 3.21.12
- `Grpc.Tools` 2.46.6

**Python Dependencies:**
```bash
pip install grpcio grpcio-tools protobuf
```

### Modifying the Protocol

1. Edit `Protos/mlbridge.proto`
2. Rebuild:
   ```bash
   ./build.sh
   ```
3. The C# stubs are auto-generated during build
4. Python stubs are regenerated by `generate_proto.py`

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Full technical roadmap and theoretical framework
- **[GRPC_MIGRATION.md](GRPC_MIGRATION.md)** - Migration guide from raw TCP to gRPC
- **[Protos/mlbridge.proto](Protos/mlbridge.proto)** - Protocol Buffer schema with inline documentation

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Implement action execution in `GrpcService.cs`
- [ ] Add map data to `StateMessage`
- [ ] Implement streaming RPCs for real-time updates
- [ ] Add more detailed pawn state (skills, gear, relationships)
- [ ] Add support for multiple maps
- [ ] Performance optimization for large colonies
- [ ] Unit tests for C# and Python

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

- **Harmony** by pardeike - Essential for all RimWorld modding
- **gRPC** by Google - High-performance RPC framework
- **Protocol Buffers** by Google - Efficient serialization

---

**Status:** ✅ Core infrastructure complete, ready for ML integration

For questions or issues, please open a GitHub issue.
