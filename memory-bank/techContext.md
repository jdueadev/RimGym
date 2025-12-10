# Technical Context

## Technologies

### C# / .NET

- **Framework**: .NET Framework 4.8 (RimWorld compatibility)
- **Language Version**: C# 7.3
- **IDE**: Visual Studio 2019+ or Rider

### Key Dependencies

```xml
<PackageReference Include="Google.Protobuf" Version="3.21.12" />
<PackageReference Include="Grpc.Core" Version="2.46.6" ExcludeAssets="native" />
<PackageReference Include="Grpc.Core.Api" Version="2.46.6" />
<PackageReference Include="Grpc.Tools" Version="2.46.6" PrivateAssets="All" />
```

**Critical**: `ExcludeAssets="native"` on Grpc.Core prevents native DLL inclusion!

### RimWorld References

```xml
<Reference Include="Assembly-CSharp">
  <HintPath>$(RimWorldPath)\RimWorldWin64_Data\Managed\Assembly-CSharp.dll</HintPath>
</Reference>
<Reference Include="UnityEngine.CoreModule">
  <HintPath>$(RimWorldPath)\RimWorldWin64_Data\Managed\UnityEngine.CoreModule.dll</HintPath>
</Reference>
<Reference Include="0Harmony">
  <HintPath>$(HarmonyPath)\0Harmony.dll</HintPath>
</Reference>
```

### Python

- **Version**: 3.8+
- **Dependencies**: `protobuf` (NOT grpcio anymore!)

### Protocol Buffers

- **Schema**: `Protos/mlbridge.proto`
- **C# Generation**: Auto via Grpc.Tools during build
- **Python Generation**: Manual via `python/generate_proto.py`

## Development Setup

### Environment Variables Required

```bash
# Linux/Mac
export RIMWORLD_DIR="/path/to/RimWorld"
export WORKSHOP_PATH="/path/to/Steam/steamapps/workshop/content/294100"
export HARMONY_PATH="$WORKSHOP_PATH/2009463077/Current/Assemblies"

# Windows (PowerShell)
$env:RIMWORLD_DIR="C:\Program Files (x86)\Steam\steamapps\common\RimWorld"
$env:WORKSHOP_PATH="C:\Program Files (x86)\Steam\steamapps\workshop\content\294100"
$env:HARMONY_PATH="$env:WORKSHOP_PATH\2009463077\Current\Assemblies"
```

### Build Commands

```bash
# Full build
dotnet build RimworldMLBridge.sln -c Release

# Python protobuf generation
cd python && python generate_proto.py

# Verification
./verify_build.sh  # Checks for native DLLs
```

### Output Structure

```
1.6/Assemblies/
├── RimworldMLBridge.dll       # ✅ Main mod
├── Google.Protobuf.dll        # ✅ Managed
├── Grpc.Core.Api.dll          # ✅ Managed
├── Grpc.Core.dll              # ✅ Managed wrapper
└── ❌ NO grpc_csharp_ext.*    # Native DLLs excluded!
```

## Technical Constraints

### Unity/RimWorld Limitations

1. **Single-Threaded**: All Unity API calls MUST be on main thread
2. **Mono Runtime**: Cannot load native C++ libraries (hence TCP not gRPC)
3. **Mod Loading**: DLLs must be in `1.6/Assemblies/` folder
4. **Harmony Limitations**: Prefix patches can block original methods

### Performance Targets

- **Serialization**: <1ms for full state
- **Throughput**: >1000 TPS per instance
- **Latency**: <100ms round-trip for actions
- **Memory**: <500MB additional RAM usage

### Security Considerations

- Server binds to localhost only (no external access)
- No authentication (assumes local trusted environment)
- Input validation on all commands before execution
- No file system access from Python client

## Development Tools

### C# Development

- **Visual Studio 2019+**: Full IDE with debugger
- **Rider**: Alternative IDE with excellent Harmony support
- **dnSpy**: For debugging RimWorld assemblies
- **ILSpy**: For decompiling Unity/RimWorld code

### Python Development

- **VSCode**: Recommended with Python extension
- **PyCharm**: Alternative IDE
- **Jupyter**: For interactive testing
- **pytest**: For unit testing

### Debugging

- **RimWorld Dev Mode**: Enable in-game console
- **Harmony Debug Logging**: Set environment variable `HARMONY_DEBUG=1`
- **TCP Packet Inspection**: Use Wireshark for protocol debugging
- **Unity Profiler**: Attach to RimWorld process (requires Unity Editor)

## Known Issues & Workarounds

### Native DLL Loading

**Issue**: RimWorld's Mono cannot load grpc_csharp_ext.dll
**Solution**: Use raw TCP with managed protobuf only

### Main Thread Access

**Issue**: Background threads can't access Unity APIs
**Solution**: Queue commands, process on Root.Update()

### Hot Reload

**Issue**: Mod code changes require RimWorld restart
**Workaround**: Use Harmony's patch debugging and test in isolation

### Protobuf Schema Evolution

**Issue**: Breaking changes require coordinated updates
**Best Practice**: Use field numbers carefully, never reuse
