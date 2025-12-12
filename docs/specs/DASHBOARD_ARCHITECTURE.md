# Dashboard Architecture Specification

**Version**: 1.0  
**Status**: Draft  
**Last Updated**: 2025-12-11

## Overview

The RimStats Dashboard is a **multi-run monitoring system** that provides real-time visualization of machine learning training sessions. It uses a **hybrid persistence strategy** (Redis + SQLite) to balance low-latency access to hot data with long-term historical analysis.

### Design Goals

1. **Multi-Run Tracking**: Single dashboard monitors multiple concurrent RimWorld training instances
2. **Real-Time Updates**: 2Hz WebSocket streams for live game state visualization
3. **Historical Analysis**: Query past episodes, compare runs, export data for offline analysis
4. **Performance**: <100ms API latency, minimal memory footprint per run
5. **Reliability**: Auto-reconnect, stale run detection, graceful degradation
6. **Scalability**: Support 5-10 concurrent runs on commodity hardware

### Non-Goals (Deferred to Future Phases)

- Authentication/authorization
- Multi-user collaboration
- Cloud deployment
- Custom alerting/notifications
- Model versioning/MLOps integration

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  RimWorld 1  │  │  RimWorld 2  │  │  RimWorld N  │          │
│  │ TCP:50051    │  │ TCP:50052    │  │ TCP:5005N    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
│                    ┌───────▼────────┐                            │
│                    │  RunManager    │                            │
│                    │  (FastAPI)     │                            │
│                    │  Port: 8000    │                            │
│                    └───────┬────────┘                            │
│                            │                                      │
│              ┌─────────────┴─────────────┐                       │
│              │                           │                       │
│         ┌────▼─────┐              ┌─────▼──────┐                │
│         │  Redis   │              │  SQLite    │                │
│         │ (Hot)    │              │ (Cold)     │                │
│         │ Port:6379│              │ dashboard. │                │
│         └────┬─────┘              │ db         │                │
│              │                    └─────┬──────┘                │
│              └────────────┬─────────────┘                        │
│                           │                                      │
│                    ┌──────▼────────┐                             │
│                    │  WebSocket +  │                             │
│                    │  REST API     │                             │
│                    └──────┬────────┘                             │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  React Frontend│
                    │  Port: 3000    │
                    └────────────────┘
```

### Component Responsibilities

#### 1. RunManager Service (Python/FastAPI)

**Purpose**: Orchestrates connections to multiple RimWorld instances and routes data to storage.

**Key Responsibilities**:

- Maintain registry of active training runs
- Create and manage SpectatorClient instances per run
- Poll each client asynchronously (100-500ms intervals)
- Transform Protobuf messages to JSON-serializable models
- Route data to Redis (hot) and SQLite (historical)
- Handle connection lifecycle (connect, disconnect, reconnect, timeout)

**Concurrency Model**:

```python
async def poll_run(run_id: str):
    while run_active(run_id):
        try:
            state = await spectator_client.get_state(timeout=1.0)
            await redis_store.push_state(run_id, state)
            await sqlite_store.log_metrics(run_id, state.metrics)
        except TimeoutError:
            mark_run_stale(run_id)
        await asyncio.sleep(0.1)  # 10Hz polling

# Launch concurrent tasks for each run
for run_id in active_runs:
    asyncio.create_task(poll_run(run_id))
```

#### 2. Redis Store (Hot Data Layer)

**Purpose**: Low-latency cache for real-time dashboard queries.

**Data Structures**:

```redis
# Current state snapshot (JSON)
SET run:{run_id}:current {serialized_game_state}
EXPIRE run:{run_id}:current 30  # 30s TTL

# Circular buffer of last 1000 states (list)
LPUSH run:{run_id}:states {state_json}
LTRIM run:{run_id}:states 0 999
EXPIRE run:{run_id}:states 604800  # 7 days

# Colonist index (hash)
HSET run:{run_id}:colonists:current {pawn_id} {colonist_json}
EXPIRE run:{run_id}:colonists:current 30

# Active threats (sorted set, score = timestamp)
ZADD run:{run_id}:threats {timestamp} {threat_json}
ZREMRANGEBYSCORE run:{run_id}:threats 0 {now - 3600}  # Keep 1h

# Metrics (time series with 1s granularity)
TS.ADD run:{run_id}:metric:reward {timestamp} {value}
TS.ADD run:{run_id}:metric:sps {timestamp} {value}

# Run metadata (hash)
HSET run:{run_id}:meta status "active"
HSET run:{run_id}:meta last_update {timestamp}
HSET run:{run_id}:meta host "integration"
HSET run:{run_id}:meta port "50051"
```

**TTL Strategy**:

- Current state: 30s (stale detection)
- State buffer: 7 days (recent history)
- Metrics: 24 hours (intraday analysis)

#### 3. SQLite Store (Historical Data Layer)

**Purpose**: Persistent storage for long-term analysis and comparisons.

**Schema**:

```sql
-- Run registry
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    name TEXT,
    algorithm TEXT,  -- PPO, A2C, DQN
    scenario TEXT,   -- colony_start, raid_defense
    host TEXT,
    port INTEGER,
    status TEXT,     -- active, completed, failed, stale
    started_at INTEGER,
    ended_at INTEGER,
    config_json TEXT  -- hyperparameters, env settings
);
CREATE INDEX idx_runs_started ON runs(started_at DESC);

-- Episode history
CREATE TABLE episodes (
    episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES runs(run_id),
    episode_num INTEGER,
    total_reward REAL,
    episode_length INTEGER,  -- steps
    started_at INTEGER,
    ended_at INTEGER,
    final_colonist_count INTEGER,
    final_wealth REAL
);
CREATE INDEX idx_episodes_run ON episodes(run_id, episode_num);

-- Aggregated metrics (hourly rollups)
CREATE TABLE metrics_hourly (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES runs(run_id),
    hour_bucket INTEGER,  -- Unix timestamp rounded to hour
    metric_name TEXT,     -- reward, sps, loss_actor, loss_critic
    min_value REAL,
    max_value REAL,
    avg_value REAL,
    count INTEGER
);
CREATE INDEX idx_metrics_run_time ON metrics_hourly(run_id, hour_bucket);

-- Incident log (raids, fires, deaths)
CREATE TABLE incidents (
    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES runs(run_id),
    timestamp INTEGER,
    incident_type TEXT,  -- raid, fire, death, mental_break
    severity TEXT,       -- minor, major, critical
    details_json TEXT    -- {enemy_count, pawn_name, etc}
);
CREATE INDEX idx_incidents_run ON incidents(run_id, timestamp DESC);

-- Colonist snapshots (sampled every 100 ticks)
CREATE TABLE colonist_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES runs(run_id),
    timestamp INTEGER,
    pawn_id INTEGER,
    pawn_name TEXT,
    health REAL,
    mood REAL,
    hunger REAL,
    rest REAL,
    job TEXT,
    skills_json TEXT  -- {shooting: 10, construction: 5, ...}
);
CREATE INDEX idx_colonist_run_time ON colonist_snapshots(run_id, timestamp);
```

**Write Pattern**:

- **Immediate**: Episodes, incidents, run lifecycle events
- **Batched** (every 10s): Metrics rollups, colonist snapshots
- **Background** (hourly): Aggregations, cleanup, vacuum

#### 4. Storage Manager (Unified Interface)

**Purpose**: Abstraction layer coordinating Redis and SQLite.

**Write-Through Pattern**:

```python
class StorageManager:
    async def store_state(self, run_id: str, state: GameState):
        # Fast path: Redis (non-blocking)
        await redis.push_state(run_id, state)
        
        # Slow path: SQLite (async, can lag)
        if state.episode_ended:
            asyncio.create_task(
                sqlite.record_episode(run_id, state.episode)
            )
        
        if state.tick % 100 == 0:  # Sample rate
            asyncio.create_task(
                sqlite.snapshot_colonists(run_id, state.colonists)
            )
```

**Read Pattern**:

```python
async def get_colonists(self, run_id: str):
    # Try hot cache first
    cached = await redis.get_colonists(run_id)
    if cached:
        return cached
    
    # Fallback to cold storage
    return await sqlite.get_latest_colonists(run_id)
```

---

## Data Flow Patterns

### 1. Real-Time State Updates

```
RimWorld Game Tick (60 Hz)
    ↓
SpectatorClient.get_state() (10 Hz poll from RunManager)
    ↓
Protobuf StateMessage
    ↓
RunManager.transform_to_json()
    ↓
        ├─→ Redis (write, <1ms)
        │   └─→ Redis Pub/Sub Channel ("run:{run_id}:updates")
        │       └─→ WebSocket ConnectionManager (broadcast to subscribers)
        │           └─→ Frontend (React state update, 2Hz)
        │
        └─→ SQLite (async task, 10-100ms)
            └─→ Background flush queue
```

**Latency Budget**:

- Game → SpectatorClient: 10-50ms (network + protobuf deserialize)
- RunManager transform: 1-5ms (protobuf → pydantic)
- Redis write: <1ms
- WebSocket broadcast: 1-10ms (per client)
- **Total (game → frontend): 20-70ms**

### 2. Historical Query Flow

```
Frontend Request: GET /api/v1/runs/{run_id}/metrics?window=1h
    ↓
FastAPI Router
    ↓
Check Redis (last 1h data)
    ├─→ Hit: Return Redis data (5-10ms)
    └─→ Miss: Query SQLite metrics_hourly table (50-200ms)
            └─→ Warm Redis cache for future requests
```

### 3. Multi-Run Comparison Flow

```
Frontend: Compare runs [run_a, run_b, run_c]
    ↓
GET /api/v1/compare?runs=run_a,run_b,run_c&metric=reward
    ↓
SQLite: Parallel queries for episode data
    ↓
Compute statistics (mean, stddev, max)
    ↓
Return aligned time-series + summary table
```

---

## WebSocket Communication Protocol

### Connection Lifecycle

**1. Client connects to `/ws/runs/{run_id}/state`**

```json
// Server → Client: Welcome message
{
    "type": "connected",
    "run_id": "run_20251211_143052_ppo_v1",
    "timestamp": 1702307452,
    "update_rate_hz": 2
}
```

**2. Server broadcasts state updates (2Hz)**

```json
{
    "type": "state_update",
    "run_id": "run_20251211_143052_ppo_v1",
    "timestamp": 1702307453,
    "frame_id": 3600,  // Game tick
    "colonists": [
        {
            "pawn_id": 101,
            "name": "Alice",
            "health": 0.95,
            "mood": 0.72,
            "job": "Hunting deer"
        }
    ],
    "resources": {
        "silver": 1200,
        "wood": 450,
        "steel": 180
    },
    "threats": [
        {
            "threat_id": "raid_001",
            "type": "raid",
            "severity": "major",
            "enemy_count": 12
        }
    ],
    "metrics": {
        "sps": 58.3,
        "queue_depth": 2,
        "action_latency_ms": 12
    }
}
```

**3. Client can request specific data**

```json
// Client → Server: Request historical data
{
    "type": "request",
    "query": "colonist_history",
    "pawn_id": 101,
    "window_seconds": 300
}

// Server → Client: Response
{
    "type": "response",
    "query": "colonist_history",
    "data": [
        {"timestamp": 1702307153, "health": 1.0, "mood": 0.85},
        {"timestamp": 1702307163, "health": 0.98, "mood": 0.83}
    ]
}
```

**4. Heartbeat mechanism**

```json
// Server → Client (every 10s)
{
    "type": "heartbeat",
    "timestamp": 1702307460
}

// Client → Server (echo)
{
    "type": "heartbeat_ack",
    "timestamp": 1702307460
}
```

**Connection timeout**: 30s without heartbeat → disconnect

### Multi-Run Aggregate Endpoint

**Endpoint**: `/ws/runs/all`

Broadcasts summary of all active runs:

```json
{
    "type": "aggregate_update",
    "timestamp": 1702307453,
    "runs": [
        {
            "run_id": "run_001",
            "status": "active",
            "colonists": 8,
            "threats": 1,
            "current_reward": 42.5,
            "sps": 58.3
        },
        {
            "run_id": "run_002",
            "status": "active",
            "colonists": 6,
            "threats": 0,
            "current_reward": 38.1,
            "sps": 61.2
        }
    ]
}
```

---

## Run Lifecycle Management

### Run States

```
┌──────────┐
│  PENDING │  (Registered but not connected)
└─────┬────┘
      │
      ▼
┌──────────┐
│  ACTIVE  │  (SpectatorClient connected, receiving data)
└─────┬────┘
      │
      ├─→ STALE (No data for 30s, retry connecting)
      │     │
      │     └─→ ACTIVE (Reconnected) or FAILED (Max retries)
      │
      ├─→ COMPLETED (Episode finished, graceful shutdown)
      │
      └─→ FAILED (Connection error, unrecoverable)
```

### Auto-Discovery Process

**Phase 1: Docker Network Scan**

```python
async def discover_runs():
    # List all containers on docker network
    containers = await docker.list_containers(network="rimworld_network")
    
    for container in containers:
        if container.labels.get("app") == "rimworld-ml":
            run_id = f"run_{container.name}_{timestamp}"
            host = container.name  # Docker DNS
            port = 50051
            
            await register_run(
                run_id=run_id,
                name=container.labels.get("run_name", run_id),
                host=host,
                port=port,
                algorithm=container.env.get("ALGORITHM", "unknown"),
                scenario=container.env.get("SCENARIO", "default")
            )
```

**Phase 2: Health Check**

```python
async def health_check_loop():
    while True:
        for run in get_active_runs():
            try:
                # Quick TCP connect test
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(run.host, run.port),
                    timeout=2.0
                )
                writer.close()
                await writer.wait_closed()
                mark_healthy(run.run_id)
            except Exception:
                mark_unhealthy(run.run_id)
        
        await asyncio.sleep(10)
```

**Phase 3: Auto-Reconnect**

```python
async def connection_monitor(run_id: str):
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            client = SpectatorClient(config)
            await client.connect()
            retry_count = 0  # Reset on success
            await poll_run(run_id, client)
        except ConnectionError:
            retry_count += 1
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
    
    mark_failed(run_id)
```

---

## REST API Specification

### Base URL: `http://localhost:8000/api/v1`

### Endpoints

#### Run Management

**GET /runs**

List all registered runs.

```json
Response 200 OK:
{
    "runs": [
        {
            "run_id": "run_20251211_143052_ppo_v1",
            "name": "PPO Baseline v1",
            "algorithm": "PPO",
            "scenario": "colony_start",
            "status": "active",
            "started_at": 1702307452,
            "colonists": 8,
            "current_reward": 42.5
        }
    ],
    "total": 1
}
```

**POST /runs**

Register a new run (manual registration).

```json
Request:
{
    "name": "Custom Run",
    "host": "192.168.1.100",
    "port": 50051,
    "algorithm": "PPO",
    "scenario": "raid_defense",
    "config": {
        "learning_rate": 3e-4,
        "gamma": 0.99
    }
}

Response 201 Created:
{
    "run_id": "run_20251211_150322_ppo_custom",
    "status": "pending"
}
```

**DELETE /runs/{run_id}**

Stop tracking a run (does not stop RimWorld, only removes from dashboard).

```json
Response 204 No Content
```

#### Game State Queries

**GET /runs/{run_id}/colonists**

Current colonists.

```json
Response 200 OK:
{
    "run_id": "run_001",
    "timestamp": 1702307453,
    "colonists": [
        {
            "pawn_id": 101,
            "name": "Alice",
            "age": 32,
            "gender": "Female",
            "health": 0.95,
            "mood": 0.72,
            "needs": {
                "food": 0.8,
                "rest": 0.6,
                "recreation": 0.3
            },
            "skills": {
                "shooting": 10,
                "construction": 5,
                "social": 7
            },
            "job": "Hunting deer",
            "position": {"x": 125.3, "y": 0, "z": 88.7}
        }
    ]
}
```

**GET /runs/{run_id}/map**

Map state overview.

```json
Response 200 OK:
{
    "run_id": "run_001",
    "map_size": {"x": 250, "z": 250},
    "buildings": 45,
    "zones": [
        {"type": "stockpile", "cells": 120},
        {"type": "growing", "cells": 300}
    ],
    "temperature": 22.5,
    "weather": "Clear"
}
```

**GET /runs/{run_id}/incidents?limit=50**

Recent incidents.

```json
Response 200 OK:
{
    "run_id": "run_001",
    "incidents": [
        {
            "incident_id": 1234,
            "timestamp": 1702307400,
            "type": "raid",
            "severity": "major",
            "details": {
                "faction": "pirate",
                "enemy_count": 12,
                "outcome": "defeated"
            }
        }
    ],
    "total": 5
}
```

#### Metrics & Training Data

**GET /runs/{run_id}/metrics?metric=reward&window=1h**

Time-series metrics.

```json
Response 200 OK:
{
    "run_id": "run_001",
    "metric": "reward",
    "window_start": 1702303852,
    "window_end": 1702307452,
    "data_points": [
        {"timestamp": 1702303852, "value": 38.2},
        {"timestamp": 1702303912, "value": 39.1},
        {"timestamp": 1702303972, "value": 40.5}
    ],
    "statistics": {
        "min": 38.2,
        "max": 45.3,
        "mean": 41.7,
        "stddev": 2.1
    }
}
```

**GET /runs/{run_id}/episodes?limit=10**

Episode history.

```json
Response 200 OK:
{
    "run_id": "run_001",
    "episodes": [
        {
            "episode_num": 42,
            "total_reward": 145.3,
            "length": 7200,
            "started_at": 1702305600,
            "ended_at": 1702307400,
            "final_colonists": 8,
            "final_wealth": 12500
        }
    ]
}
```

#### Comparison Queries

**GET /compare?runs=run_001,run_002&metric=reward**

Compare multiple runs.

```json
Response 200 OK:
{
    "metric": "reward",
    "runs": [
        {
            "run_id": "run_001",
            "algorithm": "PPO",
            "mean_reward": 41.7,
            "max_reward": 52.3,
            "total_episodes": 42
        },
        {
            "run_id": "run_002",
            "algorithm": "A2C",
            "mean_reward": 38.9,
            "max_reward": 48.1,
            "total_episodes": 38
        }
    ],
    "winner": "run_001"
}
```

---

## Performance Considerations

### Memory Management

**Per-Run Memory Budget**:

- Redis state buffer (1000 states × 50KB): ~50MB
- SpectatorClient + queues: ~10MB
- SQLite in-memory cache: ~20MB
- **Total per run: ~80MB**
- **Target capacity**: 5 concurrent runs = 400MB

**Memory Optimization Strategies**:

1. Limit state buffer size (configurable, default 1000)
2. Compress old states in SQLite (gzip JSON)
3. Evict stale runs from Redis after 7 days
4. Stream large queries (pagination, cursors)

### CPU and I/O

**CPU Bottlenecks**:

- Protobuf deserialization: ~0.5ms per state
- JSON serialization: ~1ms per state
- Redis writes: ~0.1ms per operation
- SQLite writes: 5-50ms (batched)

**I/O Optimization**:

- Redis pipelining for batch writes
- SQLite WAL mode (async writes)
- Background worker pool for SQLite (4 threads)
- Connection pooling for Redis (10 connections)

### Network Bandwidth

**Upstream (RimWorld → Dashboard)**:

- 10 Hz polling × 50KB state = 500KB/s per run
- 5 runs = 2.5MB/s = 20 Mbps

**Downstream (Dashboard → Clients)**:

- 2 Hz WebSocket × 50KB = 100KB/s per client
- 10 clients = 1MB/s = 8 Mbps

**Mitigation**:

- Delta compression for map data (only changed cells)
- Client-side caching and interpolation
- Configurable update rates

---

## Configuration

### Environment Variables

```bash
# Dashboard Backend
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000
REDIS_URL=redis://localhost:6379/0
SQLITE_PATH=/data/dashboard.db

# Data Retention
REDIS_TTL_DAYS=7
SQLITE_RETENTION_DAYS=30
STATE_BUFFER_SIZE=1000

# Performance Tuning
POLL_INTERVAL_MS=100
WEBSOCKET_UPDATE_HZ=2
MAX_CONCURRENT_RUNS=10
SQLITE_WORKER_THREADS=4

# Auto-Discovery
ENABLE_AUTO_DISCOVERY=true
DOCKER_NETWORK=rimworld_network
HEALTH_CHECK_INTERVAL_S=10
```

### Configuration File (YAML)

```yaml
dashboard:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000
    - http://localhost:8000

storage:
  redis:
    url: redis://localhost:6379/0
    ttl_days: 7
    connection_pool_size: 10
  
  sqlite:
    path: /data/dashboard.db
    retention_days: 30
    wal_mode: true
    worker_threads: 4

monitoring:
  poll_interval_ms: 100
  websocket_update_hz: 2
  max_concurrent_runs: 10
  state_buffer_size: 1000

discovery:
  enabled: true
  docker_network: rimworld_network
  health_check_interval_s: 10
  max_reconnect_attempts: 5
  reconnect_backoff_base: 2

logging:
  level: INFO
  format: json
  file: /var/log/dashboard.log
```

---

## Error Handling

### Common Failure Modes

| Error | Cause | Mitigation |
|-------|-------|-----------|
| **Connection timeout** | RimWorld not responding | Auto-reconnect with exponential backoff |
| **Stale data** | No updates for 30s | Mark run as stale, show warning in UI |
| **Redis unavailable** | Redis crashed | Fallback to SQLite for reads, queue writes for retry |
| **SQLite locked** | Concurrent write contention | Use WAL mode, retry with backoff |
| **Memory exhaustion** | Too many concurrent runs | Enforce max_concurrent_runs limit, evict oldest |
| **WebSocket disconnect** | Network issue | Client auto-reconnects, server maintains state |

### Error Response Format

```json
{
    "error": {
        "code": "RUN_NOT_FOUND",
        "message": "Run run_001 does not exist or has been removed",
        "details": {
            "run_id": "run_001"
        },
        "timestamp": 1702307452
    }
}
```

**HTTP Status Codes**:

- 400: Bad Request (invalid parameters)
- 404: Not Found (run/resource missing)
- 409: Conflict (duplicate run_id)
- 500: Internal Server Error (database error)
- 503: Service Unavailable (Redis/SQLite down)

---

## Security Considerations

### Current Phase (No Authentication)

**Assumptions**:

- Dashboard runs on trusted network (localhost or Docker internal network)
- No public exposure
- Single-user development environment

**Basic Protections**:

- CORS limited to configured origins
- Input validation on all API endpoints (Pydantic models)
- SQL injection prevention (parameterized queries)
- WebSocket connection limits (max 50 clients)

### Future Phase (Authentication Required)

**Planned Features**:

- JWT-based authentication
- API key for programmatic access
- Role-based access control (viewer, operator, admin)
- Rate limiting per user
- Audit logging

---

## Testing Strategy

### Unit Tests

**Coverage Targets**:

- Storage layer: 90%
- RunManager: 85%
- API endpoints: 90%
- WebSocket handlers: 80%

**Key Test Cases**:

- Redis circular buffer overflow
- SQLite transaction rollback on error
- WebSocket reconnection logic
- Concurrent run polling (race conditions)
- Stale run detection and cleanup

### Integration Tests

**Scenarios**:

1. **Multi-run test**: Start 2 RimWorld containers, verify dashboard tracks both
2. **Failover test**: Kill Redis, verify SQLite fallback
3. **Reconnect test**: Restart RimWorld mid-training, verify auto-reconnect
4. **Data retention test**: Fast-forward time, verify TTL and cleanup
5. **WebSocket stress test**: 20 concurrent clients, verify broadcast performance

### Performance Tests

**Benchmarks**:

- API latency (p50, p95, p99)
- WebSocket throughput (messages/second)
- Memory usage under load (5 concurrent runs, 8 hours)
- SQLite query performance (1M episodes)

---

## Deployment Architecture

### Docker Compose Services

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
  
  dashboard-backend:
    build: ./dashboard/backend
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
      - SQLITE_PATH=/data/dashboard.db
    volumes:
      - dashboard-data:/data
    networks:
      - rimworld_network
  
  dashboard-frontend:
    build: ./dashboard/frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - dashboard-backend

volumes:
  redis-data:
  dashboard-data:

networks:
  rimworld_network:
    external: true
```

### Scaling Considerations

**Current Architecture Limits**:

- Single-machine deployment
- 5-10 concurrent runs max
- ~1TB historical data (30 days retention)

**Future Horizontal Scaling** (if needed):

- Redis Cluster for sharding
- Multiple dashboard-backend replicas behind load balancer
- Shared SQLite → PostgreSQL migration
- Distributed tracing (OpenTelemetry)

---

## Appendix: Related Documents

- [TCP Protobuf Implementation](TCP_PROTOBUF_IMPLEMENTATION.md)
- [Phase V Completion Summary](../archive/PHASE_V_COMPLETE.md)
- [SpectatorClient Architecture](../../python/client/README.md)
- [RIMAPI Reference](https://ilyachichkov.github.io/RIMAPI/contributors_guide/architecture.html)

---

## Changelog

- **2025-12-11**: Initial draft (v1.0)
