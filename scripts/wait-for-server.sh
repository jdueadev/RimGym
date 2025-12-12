#!/bin/bash
# TASK-028: Wait for RimWorld TCP server to respond to QUERY_STATE
# Used by integration tests and diagnostics to ensure server is ready

set -e

HOST="${1:-localhost}"
PORT="${2:-50051}"
MAX_WAIT="${3:-60}"  # Maximum seconds to wait

echo "Waiting for RimWorld TCP server at ${HOST}:${PORT}..."
echo "Timeout: ${MAX_WAIT} seconds"

start_time=$(date +%s)
attempt=0

while true; do
    attempt=$((attempt + 1))
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -ge $MAX_WAIT ]; then
        echo "ERROR: Timeout after ${MAX_WAIT} seconds waiting for server"
        exit 1
    fi
    
    # Try to connect and send minimal data
    if timeout 5 bash -c "</dev/tcp/${HOST}/${PORT}" 2>/dev/null; then
        echo "Port ${PORT} is open (attempt ${attempt}, ${elapsed}s elapsed)"
        
        # Try to run health check if available
        if command -v uv &> /dev/null && [ -f "/app/src/RimGym/src/diagnostics/check_rimworld_health.py" ]; then
            if PYTHONPATH=/app/src uv run --project /app/src/RimGym python /app/src/RimGym/src/diagnostics/check_rimworld_health.py --single --host "$HOST" --port "$PORT" 2>/dev/null; then
                echo "✓ Server responded to QUERY_STATE"
                echo "Server is ready for connections!"
                exit 0
            else
                echo "Port open but QUERY_STATE failed, retrying..."
            fi
        else
            # If no health check available, just verify port is open
            echo "✓ Port is open (no health check script available)"
            echo "Server is ready for connections!"
            exit 0
        fi
    else
        echo "Waiting for port ${PORT}... (attempt ${attempt}, ${elapsed}s elapsed)"
    fi
    
    sleep 2
done
