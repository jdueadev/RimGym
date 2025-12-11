#!/bin/bash
# Verification script to check if native DLLs are excluded from build output

set -e

echo "========================================="
echo "Native DLL Exclusion Verification"
echo "========================================="
echo ""

ASSEMBLIES_DIR="../Assemblies"

echo "Checking $ASSEMBLIES_DIR for native DLLs..."
echo ""

# Check for native DLLs that should NOT be present
FOUND_ISSUES=0

if [ -f "$ASSEMBLIES_DIR/grpc_csharp_ext.x64.dll" ]; then
    echo "❌ FAIL: Found grpc_csharp_ext.x64.dll (should be excluded)"
    FOUND_ISSUES=1
else
    echo "✅ PASS: grpc_csharp_ext.x64.dll not found (correctly excluded)"
fi

if [ -f "$ASSEMBLIES_DIR/grpc_csharp_ext.x86.dll" ]; then
    echo "❌ FAIL: Found grpc_csharp_ext.x86.dll (should be excluded)"
    FOUND_ISSUES=1
else
    echo "✅ PASS: grpc_csharp_ext.x86.dll not found (correctly excluded)"
fi

if [ -d "$ASSEMBLIES_DIR/runtimes" ]; then
    echo "❌ FAIL: Found runtimes/ directory (should be excluded)"
    FOUND_ISSUES=1
else
    echo "✅ PASS: runtimes/ directory not found (correctly excluded)"
fi

echo ""
echo "Checking for expected managed DLLs..."
echo ""

# Check for managed DLLs that SHOULD be present
if [ -f "$ASSEMBLIES_DIR/RimworldMLBridge.dll" ]; then
    echo "✅ PASS: Found RimworldMLBridge.dll (our mod)"
else
    echo "⚠️  WARN: RimworldMLBridge.dll not found (build may not have run)"
fi

if [ -f "$ASSEMBLIES_DIR/Grpc.Core.dll" ] || [ -f "$ASSEMBLIES_DIR/Grpc.Core.Api.dll" ]; then
    echo "✅ PASS: Found Grpc.Core managed DLL(s)"
else
    echo "⚠️  WARN: Grpc.Core managed DLLs not found (build may not have run or dependencies not restored)"
fi

echo ""
echo "Listing all DLLs in Assemblies directory:"
echo ""
ls -lh "$ASSEMBLIES_DIR"/*.dll 2>/dev/null || echo "  No DLLs found"

echo ""
echo "========================================="
if [ $FOUND_ISSUES -eq 0 ]; then
    echo "✅ SUCCESS: No native DLLs found in output"
    echo "The mod should load correctly in RimWorld"
else
    echo "❌ FAILURE: Native DLLs detected"
    echo "RimWorld will fail to load the mod with BadImageFormatException"
    exit 1
fi
echo "========================================="
