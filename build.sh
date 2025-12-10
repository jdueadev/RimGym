#!/bin/bash
# Build script for RimWorld ML Bridge

set -e

echo "========================================="
echo "Building RimWorld ML Bridge with gRPC"
echo "========================================="

# Check if RIMWORLD_DIR is set
if [ -z "$RIMWORLD_DIR" ]; then
    echo "Warning: RIMWORLD_DIR environment variable is not set"
    echo "You need to set it to your RimWorld installation directory"
    echo "Example: export RIMWORLD_DIR=/path/to/RimWorld"
    echo ""
    echo "For now, using a placeholder path..."
    export RIMWORLD_DIR="/opt/rimworld"
fi

echo "RimWorld Directory: $RIMWORLD_DIR"
echo ""

# Build C# project
echo "Building C# assembly..."
cd Source
dotnet build RimworldMLBridge.csproj -c Release

if [ $? -eq 0 ]; then
    echo "✓ C# build successful"
    echo "  Output: Assemblies/RimworldMLBridge.dll"
else
    echo "✗ C# build failed"
    exit 1
fi

cd ..

# Generate Python protobuf files
echo ""
echo "Generating Python protobuf files..."
cd python
python3 generate_proto.py

if [ $? -eq 0 ]; then
    echo "✓ Python protobuf files generated"
else
    echo "✗ Python protobuf generation failed"
    exit 1
fi

cd ..

echo ""
echo "========================================="
echo "Build completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Copy the mod folder to RimWorld/Mods/"
echo "  2. Install Python dependencies: pip install -e ."
echo "  3. Run RimWorld and load a game"
echo "  4. Run the test client: python python/test_connection.py"
