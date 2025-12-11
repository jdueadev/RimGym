#!/bin/bash
# TASK-005: Log collection script for diagnostics
# Collects RimWorld server logs, system info, and diagnostic data

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="${1:-./logs/diagnostics_${TIMESTAMP}}"
CONTAINER_NAME="${2:-rimworldmlbridge-integration-1}"

echo "======================================"
echo "RimWorld ML Bridge Log Collection"
echo "======================================"
echo "Timestamp: ${TIMESTAMP}"
echo "Output: ${OUTPUT_DIR}"
echo "Container: ${CONTAINER_NAME}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Function to safely collect logs
collect_logs() {
    local source="$1"
    local dest="$2"
    local description="$3"
    
    echo "Collecting ${description}..."
    if docker cp "${CONTAINER_NAME}:${source}" "${dest}" 2>/dev/null; then
        echo "  ✓ ${description} collected"
    else
        echo "  ✗ ${description} not found or container not running"
    fi
}

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Warning: Container ${CONTAINER_NAME} is not running"
    echo "Attempting to collect from stopped container..."
fi

# Collect RimWorld logs
collect_logs "/app/rimworld.log" "${OUTPUT_DIR}/rimworld.log" "RimWorld game log"
collect_logs "/root/.config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios/Player.log" \
    "${OUTPUT_DIR}/unity_player.log" "Unity Player log"
collect_logs "/root/.config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios/Player-prev.log" \
    "${OUTPUT_DIR}/unity_player_prev.log" "Unity Player previous log"

# Collect container logs
echo "Collecting container stdout/stderr..."
docker logs "${CONTAINER_NAME}" > "${OUTPUT_DIR}/container_stdout.log" 2>&1 || \
    echo "  ✗ Container logs not available"
echo "  ✓ Container logs collected"

# Collect system info from container
echo "Collecting system information..."
docker exec "${CONTAINER_NAME}" bash -c '
echo "=== System Info ==="
uname -a
echo ""
echo "=== Memory ==="
free -h
echo ""
echo "=== Disk Space ==="
df -h /app /rimworld
echo ""
echo "=== Process List ==="
ps aux
echo ""
echo "=== Network Connections ==="
netstat -tlnp 2>/dev/null || ss -tlnp
echo ""
echo "=== Environment ==="
env | grep -E "^(DISPLAY|XVFB|RIMWORLD|DOTNET|MONO)" || true
' > "${OUTPUT_DIR}/system_info.txt" 2>&1 || echo "  ✗ System info collection failed"
echo "  ✓ System information collected"

# Run health check if available
echo "Running health check..."
if [ -f "python/diagnostics/check_rimworld_health.py" ]; then
    python python/diagnostics/check_rimworld_health.py --single --host localhost --port 50051 \
        > "${OUTPUT_DIR}/health_check.txt" 2>&1 || true
    echo "  ✓ Health check completed"
else
    echo "  ✗ Health check script not found"
fi

# Collect Docker inspect output
echo "Collecting Docker container metadata..."
docker inspect "${CONTAINER_NAME}" > "${OUTPUT_DIR}/docker_inspect.json" 2>/dev/null || \
    echo "  ✗ Docker inspect failed"
echo "  ✓ Docker metadata collected"

# Summary
echo ""
echo "======================================"
echo "Collection Complete"
echo "======================================"
echo "Files collected:"
ls -la "${OUTPUT_DIR}"
echo ""
echo "Archive created at: ${OUTPUT_DIR}"

# Create tarball for easy sharing
TAR_FILE="${OUTPUT_DIR}.tar.gz"
tar -czf "${TAR_FILE}" -C "$(dirname ${OUTPUT_DIR})" "$(basename ${OUTPUT_DIR})"
echo "Compressed archive: ${TAR_FILE}"
