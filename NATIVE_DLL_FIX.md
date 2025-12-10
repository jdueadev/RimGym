# Native DLL Loading Fix

## Problem

RimWorld was failing to load the mod with this error:
```
Exception loading grpc_csharp_ext.x64.dll: System.BadImageFormatException: Invalid Image: 
C:\gaming\steamapps\common\RimWorld\Mods\unknwn-rimworldmlbridge\Assemblies\grpc_csharp_ext.x64.dll
```

**Root Cause**: 
- `Grpc.Core` 2.46.6 includes native C++ libraries (`grpc_csharp_ext.x64.dll`, `grpc_csharp_ext.x86.dll`)
- RimWorld's mod loader attempts to load ALL DLLs in the `Assemblies/` folder as managed .NET assemblies
- Native DLLs cannot be loaded as managed assemblies, causing `BadImageFormatException`

## Solution

Modified `Source/RimworldMLBridge.csproj` with two-layer protection:

### 1. ExcludeAssets="native"
```xml
<PackageReference Include="Grpc.Core" Version="2.46.6" ExcludeAssets="native" />
```

This tells MSBuild not to copy native runtime assets from the Grpc.Core package to the output directory.

### 2. Post-Build Safety Target
```xml
<Target Name="RemoveNativeDlls" AfterTargets="Build">
  <ItemGroup>
    <NativeDllsToRemove Include="$(OutputPath)\grpc_csharp_ext*.dll" />
    <NativeDllsToRemove Include="$(OutputPath)\runtimes\**\*.dll" />
  </ItemGroup>
  <Delete Files="@(NativeDllsToRemove)" ContinueOnError="true" />
</Target>
```

This removes any native DLLs that might have been copied despite the `ExcludeAssets` setting.

## Verification

After building, verify that the `Assemblies/` folder contains:
- ✅ `RimworldMLBridge.dll` (our mod)
- ✅ `Grpc.Core.dll` (managed gRPC library)
- ✅ `Grpc.Core.Api.dll` (managed gRPC API)
- ✅ `Google.Protobuf.dll` (managed protobuf library)
- ✅ Other managed dependencies (System.Memory.dll, etc.)
- ❌ NO `grpc_csharp_ext.x64.dll` (native - should be excluded)
- ❌ NO `grpc_csharp_ext.x86.dll` (native - should be excluded)
- ❌ NO `runtimes/` folder (contains native libraries - should be excluded)

### Build Command
```bash
cd Source
dotnet build RimworldMLBridge.csproj -c Release
```

Then check:
```bash
ls -la ../Assemblies/
```

Expected output should show ONLY managed DLLs.

## Potential Impact

**Note**: Excluding native DLLs means that `Grpc.Core` may not function at runtime if it requires the native libraries. However:

1. **Immediate benefit**: The mod will successfully load in RimWorld (no more `BadImageFormatException`)
2. **Potential issue**: gRPC server functionality may fail at runtime when trying to start the server

### Runtime Behavior

If Grpc.Core requires native libraries and they're missing:
- The mod will load successfully
- The gRPC server initialization in `RimworldMLBridge.cs:StartGrpcServer()` may throw an exception
- This exception will be caught and logged, but won't crash RimWorld

### Alternative Solutions (if gRPC is essential)

If testing reveals that gRPC doesn't work without native libraries, consider:

1. **Option A**: Use `Grpc.Net.Client` instead
   - Pro: Pure managed .NET implementation, no native dependencies
   - Con: Only supports client-side, not server-side (but this project needs server-side)

2. **Option B**: Manually manage native DLLs
   - Place native DLLs in a subdirectory (e.g., `Assemblies/native/`)
   - Modify RimWorld's mod loading or use custom assembly resolver
   - Con: More complex, may not be feasible with RimWorld's mod system

3. **Option C**: Use gRPC-Web or HTTP/REST API instead
   - Pro: No native dependencies
   - Con: Requires rewriting the entire communication layer

4. **Option D**: Accept the limitation
   - Document that gRPC server won't work
   - Provide alternative integration methods

## Testing Checklist

- [ ] Build the project: `dotnet build RimworldMLBridge.csproj -c Release`
- [ ] Verify no native DLLs in `Assemblies/` folder
- [ ] Install mod in RimWorld's `Mods/` directory
- [ ] Launch RimWorld and enable the mod
- [ ] Check that mod loads without `BadImageFormatException`
- [ ] Load a game and check logs for `[MLBridge]` messages
- [ ] Test gRPC connectivity with Python client: `python python/test_connection.py`
- [ ] Verify whether gRPC server starts successfully or fails gracefully

## References

- Issue: RimWorld mod failing to load due to native DLL loading
- Package: [Grpc.Core 2.46.6](https://www.nuget.org/packages/Grpc.Core/2.46.6)
- MSBuild Assets: [Microsoft Docs](https://docs.microsoft.com/en-us/nuget/consume-packages/package-references-in-project-files)
