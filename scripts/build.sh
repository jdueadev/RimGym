#!/bin/bash
# Build script for RimTCP (RimWorld mod) + RimGym (Python client)
set -e

echo "========================================="
echo "Building RimTCP + RimGym"
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
rm -rf src/RimTCP/1.6/Assemblies/*.dll
rm -rf src/RimTCP/RimTCP/bin
rm -rf src/RimTCP/RimTCP/obj

# Build C# project
echo "Building C# assembly..."
dotnet build src/RimTCP/RimTCP/RimTCP.sln -c Release

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
python3 src/shared/python/src/generate_proto.py

if [ $? -eq 0 ]; then
    echo "✓ Python protobuf files generated"
else
    echo "❌ Python protobuf generation failed"
    exit 1
fi

echo ""
echo "========================================="
echo "✓ Build completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Install mod: ln -s $(pwd)/src/RimTCP $RIMWORLD_DIR/Mods/RimTCP"
echo "  2. Install Python deps: uv sync --project src/RimGym"
echo "  3. Start RimWorld and load a game"
echo "  4. Test connection: uv run --project src/RimGym python src/RimGym/tests/integration/test_tcp_connection.py"
