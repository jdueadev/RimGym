#!/bin/bash
set -euo pipefail

# Rebuild RimWorld Docker Volume (Linux/macOS)
#
# Use when your rimworld-data volume has stale content (e.g., legacy Mods/RimworldMLBridge).
# This will REMOVE the Docker volume and re-populate it from a local RimWorld Linux install.

RIMWORLD_SOURCE="${1:-}"
VOLUME_NAME="${2:-rimworld-data}"

if [ -z "$RIMWORLD_SOURCE" ]; then
  echo "Usage: $0 <rimworld-installation-path> [volume-name]" >&2
  exit 1
fi

echo "This will DELETE the Docker volume '$VOLUME_NAME' and all data inside it." >&2
echo "Press Enter to continue or Ctrl+C to abort." >&2
read -r

# Stop any compose stacks (best-effort)
docker compose down >/dev/null 2>&1 || true
docker-compose down >/dev/null 2>&1 || true

# Remove volume
if docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
  docker volume rm -f "$VOLUME_NAME" >/dev/null
fi

# Recreate via setup script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/setup-rimworld-volume.sh" "$RIMWORLD_SOURCE" "$VOLUME_NAME"
