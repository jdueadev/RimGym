# RimWorld ML Bridge

A RimWorld mod that provides a **TCP + Protocol Buffer** interface for machine learning agents to interact with the game. This enables training reinforcement learning agents to play RimWorld by exposing game state and accepting commands through a structured, high-performance API.

## 🎯 Project Goal

Enable autonomous AI agents to master RimWorld through deep reinforcement learning. This bridge provides the critical infrastructure to connect the Unity-based game engine with Python-based ML training frameworks.

📖 **Documentation**: See [docs/](docs/) for detailed guides and specifications.

## ✨ Features

- **TCP Server**: Low-latency, thread-safe communication (Port 50051)
- **Protocol Buffers**: Efficient binary serialization for game state
- **Dual-Mode Operation**: Training (synchronous) and Inference (asynchronous) modes
- **Game State API**: Access to colonists, health, needs, jobs, and more
- **Command Interface**: STEP, RESET, QUERY_STATE, EXECUTE_ACTION
- **Thread-Safe Design**: Background TCP thread + main thread command processing
- **Harmony Integration**: Non-invasive patching of game logic

## 🏗️ Architecture

```
┌─────────────┐      TCP + Protobuf       ┌──────────────┐
│   RimWorld  │ ◄──────────────────────► │ Python Agent │
│  (C# Mod)   │      Port 50051           │  (ML Client) │
└─────────────┘                           └──────────────┘
     ↓ Main Thread                             ↓
 [Unity APIs]                            [RL Framework]
```

### Key Design Patterns

- **Hybrid Valve**: Dual-mode tick control (training pauses game, inference runs freely)
- **Intent-Based Actions**: Semantic commands (not brittle coordinates)
- **Server-Side Validation**: Actions validated before execution
- **Length-Prefixed Framing**: Efficient TCP message delimiting

See [docs/specs/REAL_TIME_ARCHITECTURE_UPDATE.md](docs/specs/REAL_TIME_ARCHITECTURE_UPDATE.md) for detailed architecture.

### Current Status

**✅ Phase I Complete (TCP + Protobuf Foundation):**

- TCP server with length-prefixed protobuf framing
- Thread-safe command queue (Background → Main thread)
- Basic state extraction (colonists, position, health, needs)
- STEP command for tick advancement
- Training mode with game pause between steps
- Native DLL exclusion fix

**🔄 Phase II In Progress (RIMAPI Services Integration):**

- Porting robust data extraction services from RIMAPI
- High-fidelity DTOs for colonist, map, job, incident data
- Protobuf schema extensions for rich state
- Performance target: <1ms serialization

**⏳ Phase III Planned (Hybrid Valve):**

- Async mode toggle for real-time inference
- Delta compression for map updates
- Velocity vectors for latency compensation

**⏳ Phase IV Planned (Python Client):**

- Triple-threaded SpectatorClient
- Hierarchical policy (Executive/Reflex)
- Interrupt event handling

## 🚀 Quick Start

See [docs/guides/installation.md](docs/guides/installation.md) for detailed installation instructions.

### Prerequisites

- .NET SDK 4.7.2+ and RimWorld 1.6+
- Python 3.8+ with `pip install protobuf`
- Set `RIMWORLD_DIR` environment variable

### Quick Build

```bash
git clone https://github.com/jmduea/RimworldMLBridge.git
cd RimworldMLBridge
export RIMWORLD_DIR=/path/to/RimWorld
./build.sh
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

- **[Documentation Hub](docs/)** - Complete documentation index
- **[Installation Guide](docs/guides/installation.md)** - Detailed setup instructions
- **[Architecture](docs/specs/ARCHITECTURE.md)** - Deep RL theoretical framework
- **[Real-Time Architecture](docs/specs/REAL_TIME_ARCHITECTURE_UPDATE.md)** - Current implementation
- **[TCP Implementation](docs/implementation/TCP_PROTOBUF_IMPLEMENTATION.md)** - Protocol details
- **[Native DLL Fix](docs/implementation/NATIVE_DLL_FIX.md)** - Why not gRPC
- **[Memory Bank](memory-bank/)** - Project context and progress tracking
- **[Protos/mlbridge.proto](Protos/mlbridge.proto)** - Protocol Buffer schema

## 🤝 Contributing

Contributions welcome! Current priorities (Phase II):

- [ ] Port ColonistService from RIMAPI
- [ ] Port MapService from RIMAPI
- [ ] Extend Protobuf schema with rich state messages
- [ ] Implement ProtobufAdapter classes
- [ ] Add unit tests for Services and Adapters
- [ ] Performance benchmarking (<1ms serialization)
- [ ] Delta compression for async mode

See [memory-bank/progress.md](memory-bank/progress.md) for current status.

## 📝 License

[License TBD]

## 🙏 Acknowledgments

- **Harmony** by pardeike - RimWorld modding framework
- **Protocol Buffers** by Google - Efficient serialization
- **RIMAPI** project - Robust data extraction patterns

---

**Status:** ✅ Phase I Complete | 🔄 Phase II In Progress (RIMAPI Integration)

For questions or issues, please open a GitHub issue.
