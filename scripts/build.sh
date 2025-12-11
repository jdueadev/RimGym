#!/bin/bash
# Build script for RimWorld ML Bridge
set -e

echo "========================================="
echo "Building RimWorld ML Bridge"
echo "========================================="

# Verify environment
if [ -z "$RIMWORLD_DIR" ]; then
    echo "❌ ERROR: RIMWORLD_DIR environment variable not set"
    echo "   Set it with: export RIMWORLD_DIR=/path/to/RimWorld"
    exit 1
fi

echo "✓ RimWorld Directory: $RIMWORLD_DIR"
echo ""

# Clean previous build
echo "Cleaning previous build..."
rm -rf 1.6/Assemblies/*.dll
rm -rf RimworldMLBridge/bin
rm -rf RimworldMLBridge/obj

# Build C# project
echo "Building C# assembly..."
dotnet build RimworldMLBridge.sln -c Release

if [ $? -eq 0 ]; then
    echo "✓ C# build successful"
else
    echo "❌ C# build failed"
    exit 1
fi

# Verify no native DLLs
echo ""
echo "Verifying native DLL exclusion..."
if [ -f "verify_build.sh" ]; then
    ./verify_build.sh || exit 1
else
    echo "⚠️  Warning: verify_build.sh not found, skipping native DLL check"
fi

# Generate Python protobuf files
echo ""
echo "Generating Python protobuf files..."
cd python
python3 generate_proto.py

if [ $? -eq 0 ]; then
    echo "✓ Python protobuf files generated"
else
    echo "❌ Python protobuf generation failed"
    exit 1
fi

cd ..

echo ""
echo "========================================="
echo "✓ Build completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Install mod: ln -s $(pwd) $RIMWORLD_DIR/Mods/RimworldMLBridge"
echo "  2. Install Python deps: pip install -e ."
echo "  3. Start RimWorld and load a game"
echo "  4. Test connection: python python/test_tcp_connection.py"
echo ""
echo "Next steps:"
echo "  1. Copy the mod folder to RimWorld/Mods/"
echo "  2. Install Python dependencies: pip install -e ."
echo "  3. Run RimWorld and load a game"
echo "  4. Run the test client: python python/test_connection.py"
