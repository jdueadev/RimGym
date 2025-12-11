# TCP + Protocol Buffers Implementation

## Overview

RimTPC now uses **TCP sockets with Protocol Buffers** for communication instead of gRPC. This change was necessary because:

1. **gRPC requires native C++ libraries** (`grpc_csharp_ext.dll`) that cannot be loaded by RimWorld's Mono runtime
2. RimWorld's mod loader attempts to load ALL `.dll` files as managed assemblies, causing crashes with native libraries
3. TCP + Protobuf provides the same performance and type safety without native dependencies

## Architecture

### C# (RimWorld Side)

**TcpProtobufServer.cs**: Custom TCP server that:

- Listens on `localhost:50051` for Python client connections
- Uses Protocol Buffers for binary serialization (same `.proto` definitions as gRPC)
- Handles threading correctly:
  - TCP listener runs on background thread
  - Commands are queued and processed on Unity's main thread (via Harmony patch on `Root.Update()`)
  - Responses are sent back to client from background thread
- Implements length-prefixed message framing (4-byte big-endian length header)

**Key Features**:

- No native library dependencies
- Thread-safe command queue using `ConcurrentQueue<T>`
- Proper main-thread execution for all Unity/RimWorld API calls
- Supports all protobuf message types defined in `rimtcp.proto`

### Python (Client Side)

**test_tcp_connection.py**: Simple TCP client that:

- Connects to RimWorld via TCP socket
- Sends/receives length-prefixed protobuf messages
- Provides clean API: `query_state()`, `step(ticks)`, `reset()`

## Building & Running

### 1. Build the C# Mod

```powershell
cd RimTCP/RimTCP
dotnet build
```

The mod will be output to `1.6/Assemblies/` and should contain:

- ✅ `RimTCP.dll` (main mod)
- ✅ `Google.Protobuf.dll` (protobuf runtime - managed code only)
- ✅ `Grpc.Core.Api.dll` (gRPC definitions - no native code)
- ✅ `Grpc.Core.dll` (managed wrapper - won't be used but harmless)
- ❌ NO `grpc_csharp_ext.*` files (native libraries are excluded via post-build cleanup)

### 2. Generate Python Protobuf Files

```powershell
# from project root
uv run src/shared/python/src/generate_proto.py
```

This creates `rimtcp_pb2.py` from `src/shared/Protos/rimtcp.proto`.

### 3. Install Python Dependencies

```powershell
uv add protobuf
```

Note: You do NOT need `grpcio` anymore!

### 4. Start RimWorld

Load RimWorld with the mod enabled. Check the log for:

```
[RimTCP] =================================
[RimTCP] Initializing RimTCP with TCP+Protobuf...
[RimTCP] Harmony patches applied successfully
[RimTCP] TCP+Protobuf server started successfully!
[RimTCP] Listening on localhost:50051
[RimTCP] Ready for Python client connections
[RimTCP] =================================
```

### 5. Run Python Client

```powershell
uv run src/RimGym/tests/client/test_tcp_connection.py
```

Expected output:

```
Connecting to RimWorld...
Connected to RimTCP at localhost:50051

1. Querying initial state...
   Frame ID: 12345
   Is Ready: True
   Status: State retrieved
   Temperature: 21.5°C
   Weather: Clear
   Day: 1, Year: 5500
   Colonists: 3
     - Human (ID: 1001)
       Position: (128, 0, 95)
       Health: 100.0%
       Job: Mine
   ...

✓ Test successful!
```

## Protocol Details

### Message Framing

All messages use **length-prefix framing**:

```
+----------------+---------------------------+
| Length (4 bytes) | Protobuf Message (N bytes) |
| Big-Endian Int32 | Serialized Protobuf       |
+----------------+---------------------------+
```

### Request-Response Pattern

1. **Client** → **Server**: `CommandMessage`
2. **Server** → **Client**: `StateMessage`

Each request gets exactly one response.

### Supported Commands

- `QUERY_STATE`: Get current game state without advancing time
- `STEP`: Advance simulation by N ticks and return new state
- `RESET`: Reset game (not yet implemented)
- `EXECUTE_ACTION`: Execute pawn actions (not yet implemented)
- `NO_OP`: Do nothing

## Advantages Over gRPC

✅ **No native dependencies** - works with RimWorld's Mono runtime  
✅ **Same message definitions** - uses existing `.proto` file  
✅ **Same performance** - TCP + Protobuf is as fast as gRPC for our use case  
✅ **Simpler** - no need for gRPC infrastructure  
✅ **Type-safe** - Protocol Buffers provide strong typing  
✅ **Compact** - binary serialization is efficient

## Next Steps

1. Implement `ExecuteAction` to control pawns
2. Implement proper `Reset` functionality
3. Add map state observation (terrain, buildings, items)
4. Implement RL training loop integration
5. Add curriculum learning for agent training

## Troubleshooting

**"Connection refused"**: Make sure RimWorld is running and the mod loaded successfully

**"Connection closed while receiving data"**: The game may have crashed or the mod failed to load. Check `Player.log`

**Protobuf errors**: Regenerate Python files with `generate_proto.py`

**Thread-related crashes**: Commands are automatically queued and executed on the main thread - if you see thread errors, it's a bug in the server code
