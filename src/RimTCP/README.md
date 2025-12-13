# RimTCP (RimWorld Mod)

**RimTCP** is the C# mod component of the **RimGym** ecosystem. It runs inside RimWorld and provides a high-performance TCP server using Protocol Buffers to expose the game state and accept commands from external agents.

## ✨ Features

- **TCP Server**: Listens on port `50051` for incoming connections.
- **Protocol Buffers**: Uses Google Protobuf for efficient, strongly-typed binary serialization.
- **Hybrid Valve Architecture**:
  - **Training Mode**: Synchronous execution. The game pauses and waits for `STEP` commands. Ensures deterministic training.
  - **Inference Mode**: Asynchronous execution. The game runs at normal speed while the agent queries state and sends commands in real-time.
- **Thread Safety**: Decouples network I/O (background thread) from game logic (main thread) using concurrent queues.
- **Harmony Patches**: Non-invasive hooks into `TickManager` and `Root.Update` to control game flow and execute commands.

## 🏗️ Architecture

The mod operates as a bridge between the Unity game engine and the external world:

1. **Network Layer**: A background thread accepts TCP connections and deserializes length-prefixed Protobuf messages.
2. **Command Queue**: Incoming commands (`STEP`, `QUERY_STATE`, `EXECUTE_ACTION`) are queued.
3. **Main Thread Dispatch**: A Harmony patch on `Root.Update` processes the queue every frame, executing game logic safely on the main thread.
4. **State Extraction**: Services (ported from RIMAPI) extract rich game data (Colonists, Map, Items) into DTOs, which are then adapted to Protobuf messages.

## 🚀 Installation

### Prerequisites

- **RimWorld** (Version 1.6+)
- **Harmony** (Mod dependency)

### Download from Steam Workshop

- (Coming Soon)

### Manual Installation

1. Build the project (see below) or download the latest release.
2. Copy the `src/RimTCP` folder to your RimWorld `Mods` directory.
    - Windows: `C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\`
3. Enable the mod in the RimWorld Mod Manager.

## 🛠️ Building from Source

### Requirements

- .NET Framework 4.8 SDK
- Visual Studio 2022 or VS Code
- Environment variable `RIMWORLD_DIR` pointing to your RimWorld installation.

### Build Command

```powershell
# From the repository root
dotnet build src/RimTCP/RimTCP.sln -c Release
```

The build output will be placed in `src/RimTCP/1.6/Assemblies/`.

## 🧪 Testing

### Unit Tests

The solution includes a test project `RimTCP.Tests`.

```powershell
dotnet test src/RimTCP/RimTCP.Tests/RimTCP.Tests.csproj
```

### Integration Testing

See the root [Docker Documentation](../../docs/docker/README.md) for running integration tests in a containerized RimWorld environment.

### Disclaimer

- Portions of the materials used to create this content/mod are trademarks and/or copyrighted works of Ludeon Studios Inc. All rights reserved by Ludeon. This content/mod is not official and is not endorsed by Ludeon.
