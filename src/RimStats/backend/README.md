# RimWorld ML Dashboard Backend

FastAPI-based backend for the RimWorld ML training dashboard.

## Architecture

- **FastAPI**: Web framework for REST API and WebSocket endpoints
- **Redis**: Hot data cache (current states, recent metrics)
- **SQLite**: Historical data storage (episodes, aggregated metrics)
- **RunManager**: Orchestrates connections to multiple RimWorld instances
- **StorageManager**: Unified interface for Redis + SQLite

## Quick Start

### Development (Local)

```bash
# Install dependencies with uv
cd dashboard/backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Copy environment config
cp .env.example .env

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Docker)

```bash
# Build and run with docker-compose
docker-compose up dashboard-backend
```

## API Endpoints

### Run Management

- `GET /api/v1/runs` - List all training runs
- `POST /api/v1/runs` - Register a new run
- `GET /api/v1/runs/{run_id}` - Get run details
- `DELETE /api/v1/runs/{run_id}` - Unregister a run

### Game State

- `GET /api/v1/runs/{run_id}/colonists` - Get current colonists
- `GET /api/v1/runs/{run_id}/map` - Get map state
- `GET /api/v1/runs/{run_id}/incidents` - Get recent incidents
- `GET /api/v1/runs/{run_id}/threats` - Get active threats

### Metrics

- `GET /api/v1/runs/{run_id}/metrics` - Get time-series metrics
- `GET /api/v1/runs/{run_id}/episodes` - Get episode history

### WebSocket

- `WS /ws/runs/{run_id}/state` - Real-time state updates (2Hz)
- `WS /ws/runs/all` - Aggregate updates for all runs

## Development

### Testing

```bash
pytest
pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Format
black app tests

# Lint
ruff check app tests

# Type checking
mypy app
```

## Configuration

See `.env.example` for all configuration options.

## Project Structure

```
dashboard/backend/
├── app/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration
│   ├── models.py         # Pydantic models
│   ├── websocket.py      # WebSocket handlers
│   ├── routers/          # API endpoints
│   │   ├── runs.py
│   │   ├── colonists.py
│   │   ├── metrics.py
│   │   └── incidents.py
│   ├── services/         # Business logic
│   │   └── run_manager.py
│   └── storage/          # Data persistence
│       ├── redis_store.py
│       ├── sqlite_store.py
│       └── storage_manager.py
├── tests/                # Test suite
├── pyproject.toml        # Dependencies
├── Dockerfile            # Container image
└── README.md             # This file
```

## License

MIT License - See main project LICENSE

## Disclaimer

- Portions of the materials used to create this content/mod are trademarks and/or copyrighted works of Ludeon Studios Inc. All rights reserved by Ludeon. This content/mod is not official and is not endorsed by Ludeon.
