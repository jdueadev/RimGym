#!/bin/bash
set -e

# Start virtual X server for headless Unity
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!
sleep 2

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    if [ ! -z "$RIMWORLD_PID" ]; then
        kill $RIMWORLD_PID 2>/dev/null || true
    fi
    kill $XVFB_PID 2>/dev/null || true
}
trap cleanup EXIT

case "$1" in
    test)
        echo "Running automated test suite..."
        
        # Check if RimWorld is installed
        if [ ! -f "${RIMWORLD_PATH}/RimWorldLinux" ]; then
            echo ""
            echo "ERROR: RimWorld not found at ${RIMWORLD_PATH}"
            echo "The rimworld-data volume appears to be empty."
            echo ""
            echo "Please run the setup script first:"
            echo "  .\\docker\\setup-rimworld-volume.ps1 \"C:\\RimworldLinux\""
            exit 1
        fi
        
        # Install Harmony dependency (required by our mod)
        # We'll create a minimal Harmony mod structure with About.xml and the DLL
        if [ ! -d "${RIMWORLD_PATH}/Mods/HarmonyMod" ]; then
            echo "Installing Harmony mod dependency..."
            mkdir -p ${RIMWORLD_PATH}/Mods/HarmonyMod/About
            mkdir -p ${RIMWORLD_PATH}/Mods/HarmonyMod/Assemblies
            
            # Create About.xml for Harmony
            cat > ${RIMWORLD_PATH}/Mods/HarmonyMod/About/About.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <name>Harmony</name>
    <author>Andreas Pardeike</author>
    <packageId>brrainz.harmony</packageId>
    <supportedVersions>
        <li>1.6</li>
    </supportedVersions>
    <description>Harmony library for RimWorld modding</description>
    <url>https://github.com/pardeike/HarmonyRimWorld</url>
</ModMetaData>
EOF
            
            # Copy Harmony DLL (we already have it from our build)
            cp /app/1.6/Assemblies/0Harmony.dll ${RIMWORLD_PATH}/Mods/HarmonyMod/Assemblies/
            echo "✓ Harmony installed"
        fi
        
        # Install mod to RimWorld Mods directory (mod is in /app from build)
        echo "Installing RimworldMLBridge mod..."
        mkdir -p ${RIMWORLD_PATH}/Mods/RimworldRimGym
        cp -r /app/1.6 ${RIMWORLD_PATH}/Mods/RimworldMLBridge/
        cp -r /app/About ${RIMWORLD_PATH}/Mods/RimworldMLBridge/
        echo "✓ Mod installed to ${RIMWORLD_PATH}/Mods/RimworldMLBridge"
        
        # Create ModsConfig.xml to enable our mods
        echo "Creating ModsConfig.xml..."
        mkdir -p "/root/.config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios/Config"
        cat > "/root/.config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<ModsConfigData>
  <version>1.6.7146 rev475</version>
  <activeMods>
    <li>Ludeon.RimWorld</li>
    <li>Ludeon.RimWorld.Royalty</li>
    <li>Ludeon.RimWorld.Ideology</li>
    <li>Ludeon.RimWorld.Biotech</li>
    <li>Ludeon.RimWorld.Anomaly</li>
    <li>Ludeon.RimWorld.Odyssey</li>
    <li>brrainz.harmony</li>
    <li>unknwnentity.rimworldmlbridge</li>
  </activeMods>
</ModsConfigData>
EOF
        echo "✓ ModsConfig.xml created"
        
        # Launch RimWorld in background (headless mode)
        echo "Launching RimWorld (headless mode)..."
        cd ${RIMWORLD_PATH}
        ./RimWorldLinux \
            -batchmode \
            -nographics \
            -quicktest \
            -logfile /app/rimworld.log &
        RIMWORLD_PID=$!
        
        # Wait a moment for startup
        sleep 5
        
        # Run tests
        cd /app
        uv run python python/test_automated_suite.py \
            --no-launch \
            --output test_results.txt
        
        TEST_EXIT_CODE=$?
        
        # Show logs on failure
        if [ $TEST_EXIT_CODE -ne 0 ]; then
            echo "Tests failed! RimWorld log:"
            tail -n 100 /app/rimworld.log
        fi
        
        exit $TEST_EXIT_CODE
        ;;
        
    build)
        echo "Building C# project..."
        cd /app
        dotnet build RimworldMLBridge.sln -c Release
        ;;
        
    interactive)
        echo "Starting interactive mode..."
        exec /bin/bash
        ;;
        
    *)
        echo "Usage: docker run rimworld-ml-bridge [test|build|interactive]"
        exit 1
        ;;
esac
