# RimStats

Real-time training visualization dashboard for RimGym.

## Architecture

This dashboard is a **multi-run monitoring system** with hybrid persistence (Redis + SQLite):

- **Backend**: FastAPI (Python) serving REST API + WebSocket
- **Frontend**: React + TypeScript with Plotly charts
- **Storage**: Redis (hot data) + SQLite (historical data)

See [docs/specs/DASHBOARD_ARCHITECTURE.md](../docs/specs/DASHBOARD_ARCHITECTURE.md) for complete architecture specification.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- Node.js 20+ (for frontend development)

### Run with Docker Compose

```bash
# From project root
docker-compose up redis dashboard-backend dashboard-frontend

# Access dashboard at http://localhost:3000
# API docs at http://localhost:8000/docs
```

### Local Development

**Backend:**

```bash
cd dashboard/backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd dashboard/frontend
npm install
npm start
```

## Features

### Current (Phase 1)

✅ FastAPI backend scaffolding  
✅ REST API endpoints (runs, colonists, metrics, incidents)  
✅ WebSocket support for real-time updates  
✅ React frontend scaffolding  
✅ Docker containers with multi-stage builds  
✅ Hybrid storage architecture (Redis + SQLite)  

### Planned

- [ ] RunManager with SpectatorClient integration
- [ ] Redis circular buffer implementation
- [ ] SQLite schema and persistence
- [ ] Auto-discovery of RimWorld containers
- [ ] Frontend components (colonist list, charts, threat monitor)
- [ ] Multi-run comparison view
- [ ] Data retention and cleanup

## Project Structure

```
dashboard/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # Application entry
│   │   ├── config.py    # Configuration
│   │   ├── models.py    # Pydantic models
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── storage/     # Data persistence
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/             # React frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   └── contexts/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
└── README.md             # This file
```

## Documentation

- [Dashboard Architecture](../docs/specs/DASHBOARD_ARCHITECTURE.md) - Complete technical specification
- [Backend README](backend/README.md) - Backend development guide
- [Frontend README](frontend/README.md) - Frontend development guide
- [Dashboard Usage Guide](../docs/guides/dashboard_usage.md) - User guide (coming soon)

## License

MIT License - See main project LICENSE

## Disclaimer

- Portions of the materials used to create this content/mod are trademarks and/or copyrighted works of Ludeon Studios Inc. All rights reserved by Ludeon. This content/mod is not official and is not endorsed by Ludeon.
