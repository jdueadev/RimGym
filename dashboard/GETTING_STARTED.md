# RimWorld ML Dashboard - Getting Started

## Quick Start Guide

### 1. Start the Dashboard

```bash
cd dashboard
docker-compose up -d
```

This starts:
- **Redis**: Hot data storage (port 6379)
- **Backend**: FastAPI server (port 8000)  
- **Frontend**: React app (port 3000)

### 2. Access the Dashboard

Open your browser to http://localhost:3000

### 3. Register a Training Run

The dashboard will automatically discover RimWorld instances on the `rimworld_network` Docker network. You can also manually register a run:

```bash
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run_test_001",
    "name": "PPO Test Run",
    "algorithm": "PPO",
    "scenario": "colony_start",
    "status": "pending",
    "host": "localhost",
    "port": 50051,
    "started_at": '$(date +%s)',
    "config": {}
  }'
```

### 4. Monitor Your Training

The dashboard will:
- Connect to the RimWorld instance via TCP
- Poll game state every 100ms
- Display real-time colonist counts, rewards, and status
- Store historical data for analysis

## What to Expect

### Dashboard Features

**Run Cards**: Each active training run gets a card showing:
- Run name and ID
- Algorithm and scenario
- Current status (active/stale/completed)
- Colonist count
- Current reward
- Connection info

**Quick Stats**: Aggregate statistics across all runs:
- Total active runs
- Total colonists
- Average reward

### Data Flow

1. **RimWorld Game** runs with ML Bridge mod
2. **SpectatorClient** (in backend) connects and polls state
3. **Redis** caches hot data (last 1000 states)
4. **SQLite** stores historical episodes and metrics
5. **Frontend** displays real-time updates via polling

## Development Setup

### Backend Development

```bash
cd backend
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

Edit `src/App.tsx` to modify the UI.

## Next Steps

- View API documentation: http://localhost:8000/docs
- Check backend logs: `docker-compose logs dashboard-backend`
- Monitor Redis: `docker-compose exec redis redis-cli monitor`
- Query SQLite: `sqlite3 data/dashboard.db "SELECT * FROM runs;"`

## Troubleshooting

**No runs showing up?**
- Check if RimWorld is running with the ML Bridge mod
- Verify the port (default 50051) is accessible
- Check backend logs for connection errors

**Frontend not loading?**
- Check if backend is running: `curl http://localhost:8000/health`
- Verify CORS settings in backend config

**Performance issues?**
- Reduce poll frequency in `config.py`
- Limit number of concurrent runs
- Check Redis memory usage

## Configuration

Edit `backend/app/config.py` or use environment variables:

```bash
# Polling frequency
POLL_INTERVAL_MS=100

# WebSocket update rate
WEBSOCKET_UPDATE_HZ=2

# Max concurrent runs
MAX_CONCURRENT_RUNS=10

# Data retention
REDIS_TTL_DAYS=7
SQLITE_RETENTION_DAYS=30
```

## Architecture

See [DASHBOARD_ARCHITECTURE.md](../docs/specs/DASHBOARD_ARCHITECTURE.md) for complete technical specification.
