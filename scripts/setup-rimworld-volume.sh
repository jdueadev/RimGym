#!/bin/bash
# Setup script to create RimWorld Docker volume from local installation

set -e

RIMWORLD_SOURCE="$1"
VOLUME_NAME="${2:-rimworld-data}"

if [ -z "$RIMWORLD_SOURCE" ]; then
    echo "Usage: $0 <rimworld-installation-path> [volume-name]"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/Steam/steamapps/common/RimWorld"
    echo "  $0 ~/Games/RimWorld rimworld-data"
    exit 1
fi

if [ ! -d "$RIMWORLD_SOURCE" ]; then
    echo "ERROR: RimWorld directory not found: $RIMWORLD_SOURCE"
    exit 1
fi

if [ ! -f "$RIMWORLD_SOURCE/RimWorldLinux" ]; then
    echo "ERROR: RimWorldLinux executable not found in: $RIMWORLD_SOURCE"
    echo "Make sure you're pointing to the Linux version of RimWorld"
    exit 1
fi

echo "Setting up RimWorld Docker volume..."
echo "Source: $RIMWORLD_SOURCE"
echo "Volume: $VOLUME_NAME"
echo ""

# Create volume if it doesn't exist
if ! docker volume inspect $VOLUME_NAME &>/dev/null; then
    echo "Creating Docker volume: $VOLUME_NAME"
    docker volume create $VOLUME_NAME
fi

# Copy RimWorld to volume
echo "Copying RimWorld files to Docker volume (this may take a minute)..."
docker run --rm \
    -v "$RIMWORLD_SOURCE:/source:ro" \
    -v "$VOLUME_NAME:/dest" \
    alpine sh -c "cp -r /source/. /dest/ && rm -rf /dest/Mods/RimworldMLBridge /dest/Mods/RimWorldMLBridge || true && chmod +x /dest/RimWorldLinux"

echo ""
echo "✅ RimWorld Docker volume setup complete!"
echo ""
echo "Verify with:"
echo "  docker run --rm -v $VOLUME_NAME:/opt/rimworld alpine ls -la /opt/rimworld"
echo ""
echo "Use in tests:"
echo "  docker-compose up test"
echo "  or"
echo "  docker compose up test"
