# gRPC + Protocol Buffers Migration

This document describes the migration from raw TCP messaging to gRPC with Protocol Buffers.

## Changes Made

### 1. Protocol Definition (`Protos/mlbridge.proto`)

Defined structured messages using Protocol Buffers:
- **TickMessage**: Game tick notifications
- **AckMessage**: Acknowledgments 
- **CommandMessage**: Commands from agent to game (STEP, RESET, QUERY_STATE, etc.)
- **StateMessage**: Game state information
- **Entity**: Pawn/object state with position, health, needs, etc.
- **Action**: Individual pawn actions (GOTO, ATTACK, BUILD, etc.)

### 2. C# Implementation

**New Files:**
- `Source/GrpcService.cs`: Implementation of the MLBridge gRPC service
- `Source/RimworldMLBridge.csproj`: Build configuration with gRPC/Protobuf packages

**Modified Files:**
- `Source/RimworldMLBridge.cs`: Replaced raw TCP server with gRPC server
- `Source/TickPatch.cs`: Simplified to log ticks (clients now poll via gRPC)

**Key Changes:**
- Port changed from 9876 (TCP) to 50051 (standard gRPC)
- Server starts automatically on mod load
- Supports multiple concurrent clients
- Type-safe message passing

### 3. Python Client

**Modified Files:**
- `python/test_connection.py`: Complete rewrite to use gRPC
- `pyproject.toml`: Added gRPC dependencies

**New Files:**
- `python/generate_proto.py`: Script to generate Python protobuf files

**Key Changes:**
- Uses `grpcio` and `grpcio-tools` packages
- Generated client stubs from `.proto` file
- Type-safe request/response handling
- Better error handling with gRPC status codes

## Building

### Prerequisites

**C# (RimWorld Mod):**
- .NET SDK 4.7.2 or higher
- RimWorld installation (set `RIMWORLD_DIR` environment variable)
- Packages installed automatically via NuGet:
  - `Grpc.Core` 2.46.6
  - `Google.Protobuf` 3.21.12
  - `Grpc.Tools` 2.46.6

**Python (Client):**
- Python 3.8+
- Install dependencies: `pip install -e .`

### Build Steps

1. **Set RimWorld directory:**
   ```bash
   export RIMWORLD_DIR=/path/to/RimWorld
   ```

2. **Build everything:**
   ```bash
   ./build.sh
   ```

   Or manually:

3. **Build C# mod:**
   ```bash
   cd Source
   dotnet build RimworldMLBridge.csproj -c Release
   ```

4. **Generate Python protobuf files:**
   ```bash
   cd python
   python generate_proto.py
   ```

## Usage

### 1. Install the Mod

Copy the entire mod folder to `RimWorld/Mods/RimworldMLBridge/`

### 2. Start RimWorld

Load a game. Check the log for:
```
[MLBridge] gRPC server started successfully!
[MLBridge] Listening on localhost:50051
```

### 3. Run Python Client

```bash
cd python
python test_connection.py
```

The client will:
- Connect to the gRPC server
- Poll game state every 5 seconds
- Display pawn information (health, mood, current job)
- Send tick acknowledgments
- Execute NO-OP commands

## API Reference

### gRPC Service Methods

#### `SendTick(TickMessage) → AckMessage`
Send a tick notification to the agent.

#### `ExecuteCommand(CommandMessage) → StateMessage`
Execute a command and return the resulting game state.
- Command types: `NO_OP`, `STEP`, `RESET`, `QUERY_STATE`, `EXECUTE_ACTION`

#### `GetState(EmptyMessage) → StateMessage`
Get the current game state including:
- Global state (day, year, temperature)
- All colonist pawns with their:
  - Position
  - Health
  - Needs (mood, hunger, rest)
  - Current job
  - Draft status

## Advantages Over Raw TCP

1. **Type Safety**: Protocol Buffers provide compile-time type checking
2. **Efficiency**: Binary serialization is faster and more compact than text
3. **Versioning**: Proto files can evolve with backward compatibility
4. **Auto-generated Code**: Client/server stubs generated automatically
5. **Better Error Handling**: gRPC provides rich status codes and metadata
6. **Multiple Clients**: gRPC server can handle concurrent connections
7. **Streaming Support**: Can add streaming RPCs in the future for real-time updates

## Future Enhancements

- **Server Streaming**: Stream tick updates to clients instead of polling
- **Bidirectional Streaming**: Real-time command execution with state updates
- **Action Execution**: Implement actual pawn job execution from Action messages
- **Map Data**: Add terrain and building data to StateMessage
- **Authentication**: Add TLS and authentication for remote connections

## Migration Notes

### Breaking Changes

- **Port**: Changed from 9876 to 50051
- **Protocol**: No longer compatible with raw TCP clients
- **Messages**: Must use protobuf messages instead of string parsing

### Backward Compatibility

The old raw TCP implementation has been completely removed. If you need to support both:
1. Keep old `RimworldMLBridge.cs` as `RimworldMLBridge_TCP.cs`
2. Use a config file to choose protocol at runtime
3. Implement both in parallel on different ports

## Troubleshooting

### C# Build Issues

**"Could not find RimWorld assemblies"**
- Set `RIMWORLD_DIR` environment variable
- Check paths in `RimworldMLBridge.csproj`

**"Grpc.Core not found"**
- Run `dotnet restore` in Source directory
- Check NuGet package sources

### Python Issues

**"No module named 'mlbridge_pb2'"**
- Run `python generate_proto.py` in python directory
- Ensure `grpcio-tools` is installed

**"Connection refused"**
- Ensure RimWorld is running with the mod loaded
- Check RimWorld's Player.log for [MLBridge] messages
- Verify port 50051 is not blocked by firewall

**"RPC failed with status UNAVAILABLE"**
- RimWorld may have crashed or mod failed to load
- Check for errors in Player.log
- Restart RimWorld and try again

## Performance Notes

- gRPC uses HTTP/2 multiplexing for efficient connection usage
- Protocol Buffers are ~3-10x more efficient than JSON/text
- Binary encoding reduces network bandwidth by ~50-70%
- Consider using streaming RPCs for high-frequency updates (>10 Hz)
