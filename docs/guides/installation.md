# Installation Guide

## Prerequisites

### For C# Development

- .NET SDK 4.7.2 or higher
- RimWorld 1.6+ installation
- Visual Studio 2019+ or JetBrains Rider (optional, for development)

### For Python Client

- Python 3.8+
- pip package manager

## Step-by-Step Installation

### 1. Clone Repository

```bash
git clone https://github.com/jmduea/RimworldMLBridge.git
cd RimworldMLBridge
```

### 2. Set Environment Variables

#### Linux/Mac

```bash
export RIMWORLD_DIR="/path/to/RimWorld"
export WORKSHOP_PATH="/path/to/Steam/steamapps/workshop/content/294100"
export HARMONY_PATH="$WORKSHOP_PATH/2009463077/Current/Assemblies"
```

#### Windows (PowerShell)

```powershell
$env:RIMWORLD_DIR="C:\Program Files (x86)\Steam\steamapps\common\RimWorld"
$env:WORKSHOP_PATH="C:\Program Files (x86)\Steam\steamapps\workshop\content\294100"
$env:HARMONY_PATH="$env:WORKSHOP_PATH\2009463077\Current\Assemblies"
```

**Note**: Adjust paths based on your Steam installation directory.

### 3. Build the Mod

#### Linux/Mac

```bash
chmod +x build.sh
./build.sh
```

#### Windows

```powershell
# Build using dotnet CLI
dotnet build RimworldMLBridge.sln -c Release

# Generate Python protobuf files
cd python
python generate_proto.py
cd ..
```

### 4. Install Mod to RimWorld

#### Option A: Symlink (Recommended for Development)

**Linux/Mac:**

```bash
ln -s "$(pwd)" "$RIMWORLD_DIR/Mods/RimworldMLBridge"
```

**Windows (PowerShell as Administrator):**

```powershell
New-Item -ItemType SymbolicLink -Path "$env:RIMWORLD_DIR\Mods\RimworldMLBridge" -Target (Get-Location).Path
```

#### Option B: Copy (For Production)

**Linux/Mac:**

```bash
cp -r . "$RIMWORLD_DIR/Mods/RimworldMLBridge"
```

**Windows:**

```powershell
Copy-Item -Path . -Destination "$env:RIMWORLD_DIR\Mods\RimworldMLBridge" -Recurse -Force
```

### 5. Install Python Client

```bash
# Install in development mode
pip install -e .

# Or install dependencies only
pip install protobuf
```

### 6. Verify Installation

#### Start RimWorld

1. Launch RimWorld
2. Go to **Mods** menu
3. Enable "RimWorld ML Bridge" in the mod list
4. Ensure "Harmony" mod is also enabled (it's a dependency)
5. Restart RimWorld if prompted
6. Load or start a new game

#### Check the Log

Look for these messages in the RimWorld log (accessible via Dev Mode → Debug Log):

```
[MLBridge] Mod initialized successfully
[MLBridge] TCP+Protobuf server started successfully!
[MLBridge] Listening on localhost:50051
```

#### Test Connection

Run the test client to verify the connection:

```bash
cd python
python test_tcp_connection.py
```

**Expected output:**

```
Connecting to RimWorld...
Connected to RimWorld ML Bridge at localhost:50051
Frame ID: 12345
Colonists: 3
  - Human (ID: 1001) Health: 100.0%
  - Human (ID: 1002) Health: 95.2%
  - Human (ID: 1003) Health: 100.0%
✓ Test successful!
```

## Troubleshooting

### "Could not load 0Harmony.dll"

**Cause**: Harmony mod is not installed or not found.

**Solution**:

1. Install Harmony mod from Steam Workshop (ID: 2009463077)
2. Verify `HARMONY_PATH` environment variable points to correct location
3. Check that `0Harmony.dll` exists at `$HARMONY_PATH/0Harmony.dll`

### "BadImageFormatException" or "Could not load grpc_csharp_ext"

**Cause**: Native DLLs were included in the build output.

**Solution**:

1. Run verification script:

   ```bash
   ./verify_build.sh  # Linux/Mac
   # or
   Get-ChildItem 1.6\Assemblies\*.dll | Where-Object { $_.Name -like "*csharp_ext*" }  # Windows
   ```

2. If native DLLs are found, rebuild:

   ```bash
   dotnet clean
   ./build.sh  # or dotnet build for Windows
   ```

3. Verify `RimworldMLBridge.csproj` has `ExcludeAssets="native"` on Grpc.Core reference

### "Connection refused" in Python Client

**Cause**: RimWorld is not running, mod is not loaded, or game is not started.

**Solution**:

1. Ensure RimWorld is running
2. Load a game (server doesn't start in main menu)
3. Check RimWorld log for "[MLBridge] TCP+Protobuf server started"
4. Verify nothing else is using port 50051:

   ```bash
   # Linux/Mac
   lsof -i :50051
   
   # Windows
   netstat -ano | findstr :50051
   ```

5. Check firewall settings (Windows may block localhost connections)

### Build Fails: "RimWorld assemblies not found"

**Cause**: `RIMWORLD_DIR` not set or pointing to wrong location.

**Solution**:

1. Verify RimWorld installation directory
2. Update environment variables
3. Check paths in `RimworldMLBridge.csproj`:

   ```xml
   <RimWorldPath>$(RIMWORLD_DIR)</RimWorldPath>
   ```

4. Try setting path directly in `.csproj` if environment variable doesn't work

### Python Import Error: "No module named 'mlbridge_pb2'"

**Cause**: Protobuf files not generated.

**Solution**:

```bash
cd python
python generate_proto.py
```

Verify `mlbridge_pb2.py` is created in the `python/` directory.

### Mod Doesn't Appear in RimWorld

**Cause**: Mod not in correct directory or `About.xml` is malformed.

**Solution**:

1. Verify mod is in `$RIMWORLD_DIR/Mods/RimworldMLBridge/`
2. Check directory structure:

   ```
   RimworldMLBridge/
   ├── About/
   │   └── About.xml
   └── 1.6/
       └── Assemblies/
           └── RimworldMLBridge.dll
   ```

3. Verify `About.xml` is valid XML

## Next Steps

Once installation is complete:

- Read the [Python Client Guide](python-client.md) for usage examples (Coming Soon)
- Review the [Architecture Overview](../specs/ARCHITECTURE.md) to understand the system
- Check the [Memory Bank](../../memory-bank/) for current project status
- Explore example training scripts (Coming Soon)

## Getting Help

- Check [Troubleshooting Guide](troubleshooting.md) for common issues (Coming Soon)
- Review [GitHub Issues](https://github.com/jmduea/RimworldMLBridge/issues) for known problems
- Submit new issues with detailed error logs and environment info
