"""Storage manager - unified interface for Redis + SQLite"""

import asyncio
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages hybrid Redis + SQLite storage"""

    def __init__(self, redis_url: str, sqlite_path: str) -> None:
        self.redis_url = redis_url
        self.sqlite_path = sqlite_path
        self.redis_client: Optional[redis.Redis] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None

        # Configuration
        self.state_buffer_size = 1000
        self.redis_ttl_seconds = 7 * 24 * 3600  # 7 days

    async def initialize(self) -> None:
        """Initialize storage connections"""
        # Connect to Redis
        try:
            self.redis_client = redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        # Initialize SQLite
        try:
            db_path = Path(self.sqlite_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Use asyncio to run blocking SQLite operations
            self.sqlite_conn = sqlite3.connect(str(db_path), check_same_thread=False)
            self.sqlite_conn.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrency
            self.sqlite_conn.execute("PRAGMA journal_mode=WAL")

            # Create tables
            await self._create_tables()
            logger.info(f"Initialized SQLite database at {self.sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            raise

    async def close(self) -> None:
        """Close storage connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")

        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("Closed SQLite connection")

    async def _create_tables(self) -> None:
        """Create SQLite tables"""
        await asyncio.get_event_loop().run_in_executor(None, self._create_tables_sync)

    def _create_tables_sync(self) -> None:
        """Create SQLite tables (synchronous)"""
        cursor = self.sqlite_conn.cursor()

        # Runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                algorithm TEXT,
                scenario TEXT,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                status TEXT NOT NULL,
                started_at INTEGER NOT NULL,
                ended_at INTEGER,
                config_json TEXT
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at DESC)"
        )

        # Episodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                episode_num INTEGER NOT NULL,
                total_reward REAL,
                episode_length INTEGER,
                started_at INTEGER,
                ended_at INTEGER,
                final_colonist_count INTEGER,
                final_wealth REAL,
                UNIQUE(run_id, episode_num)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episodes_run ON episodes(run_id, episode_num)"
        )

        # Incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                timestamp INTEGER NOT NULL,
                incident_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                details_json TEXT
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidents_run ON incidents(run_id, timestamp DESC)"
        )

        # Metrics hourly rollups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_hourly (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                hour_bucket INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                min_value REAL,
                max_value REAL,
                avg_value REAL,
                count INTEGER,
                UNIQUE(run_id, hour_bucket, metric_name)
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_run_time ON metrics_hourly(run_id, hour_bucket)"
        )

        # Colonist snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS colonist_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                timestamp INTEGER NOT NULL,
                pawn_id INTEGER NOT NULL,
                pawn_name TEXT,
                health REAL,
                mood REAL,
                hunger REAL,
                rest REAL,
                job TEXT,
                skills_json TEXT
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_colonist_run_time ON colonist_snapshots(run_id, timestamp)"
        )

        self.sqlite_conn.commit()

    async def push_state(self, run_id: str, state: Dict[str, Any]) -> None:
        """Store game state (Redis for hot data)"""
        if not self.redis_client:
            return

        try:
            pipe = self.redis_client.pipeline()

            # Current state snapshot
            pipe.set(
                f"run:{run_id}:current",
                json.dumps(state),
                ex=30,  # 30s TTL
            )

            # Circular buffer of states
            pipe.lpush(f"run:{run_id}:states", json.dumps(state))
            pipe.ltrim(f"run:{run_id}:states", 0, self.state_buffer_size - 1)
            pipe.expire(f"run:{run_id}:states", self.redis_ttl_seconds)

            # Update run metadata
            pipe.hset(f"run:{run_id}:meta", "last_update", int(time.time()))
            pipe.hset(f"run:{run_id}:meta", "status", "active")

            await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to push state to Redis: {e}")

    async def get_current_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get current state snapshot"""
        if not self.redis_client:
            return None

        try:
            data = await self.redis_client.get(f"run:{run_id}:current")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get current state: {e}")
            return None

    async def get_colonists(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get current colonists (Redis first, SQLite fallback)"""
        # Try Redis first
        state = await self.get_current_state(run_id)
        if state and "colonists" in state:
            return {
                "run_id": run_id,
                "colonists": state["colonists"],
                "timestamp": state.get("timestamp"),
            }

        # Fallback to SQLite
        try:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqlite_conn.execute(
                    """
                    SELECT pawn_id, pawn_name, health, mood, hunger, rest, job, skills_json
                    FROM colonist_snapshots
                    WHERE run_id = ? AND timestamp = (
                        SELECT MAX(timestamp) FROM colonist_snapshots WHERE run_id = ?
                    )
                    """,
                    (run_id, run_id),
                ),
            )
            rows = cursor.fetchall()
            if rows:
                colonists = [dict(row) for row in rows]
                return {"run_id": run_id, "colonists": colonists}
        except Exception as e:
            logger.error(f"Failed to get colonists from SQLite: {e}")

        return None

    async def get_metrics(
        self, run_id: str, metric: str, window_seconds: int
    ) -> Optional[Dict[str, Any]]:
        """Get time-series metrics"""
        # For now, return placeholder
        # TODO: Implement Redis time-series or SQLite query
        return {
            "run_id": run_id,
            "metric": metric,
            "window_start": int(time.time()) - window_seconds,
            "window_end": int(time.time()),
            "data_points": [],
            "statistics": {},
        }

    async def get_episodes(self, run_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get episode history"""
        try:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqlite_conn.execute(
                    """
                    SELECT episode_num, total_reward, episode_length, started_at, ended_at,
                           final_colonist_count, final_wealth
                    FROM episodes
                    WHERE run_id = ?
                    ORDER BY episode_num DESC
                    LIMIT ?
                    """,
                    (run_id, limit),
                ),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get episodes: {e}")
            return []

    async def get_incidents(self, run_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get recent incidents"""
        try:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqlite_conn.execute(
                    """
                    SELECT incident_id, timestamp, incident_type, severity, details_json
                    FROM incidents
                    WHERE run_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (run_id, limit),
                ),
            )
            rows = cursor.fetchall()
            incidents = []
            for row in rows:
                incident = dict(row)
                if incident.get("details_json"):
                    incident["details"] = json.loads(incident["details_json"])
                    del incident["details_json"]
                incidents.append(incident)
            return incidents
        except Exception as e:
            logger.error(f"Failed to get incidents: {e}")
            return []

    async def get_active_threats(self, run_id: str) -> List[Dict[str, Any]]:
        """Get active threats from Redis"""
        if not self.redis_client:
            return []

        try:
            # Get threats from sorted set (score = timestamp)
            now = int(time.time())
            threats = await self.redis_client.zrangebyscore(
                f"run:{run_id}:threats",
                now - 3600,  # Last hour
                now,
                withscores=True,
            )
            return [json.loads(threat[0]) for threat in threats]
        except Exception as e:
            logger.error(f"Failed to get active threats: {e}")
            return []

    async def record_episode(self, run_id: str, episode_data: Dict[str, Any]) -> None:
        """Record completed episode to SQLite"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqlite_conn.execute(
                    """
                    INSERT OR REPLACE INTO episodes 
                    (run_id, episode_num, total_reward, episode_length, started_at, ended_at,
                     final_colonist_count, final_wealth)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        episode_data.get("episode_num"),
                        episode_data.get("total_reward"),
                        episode_data.get("episode_length"),
                        episode_data.get("started_at"),
                        episode_data.get("ended_at"),
                        episode_data.get("final_colonist_count"),
                        episode_data.get("final_wealth"),
                    ),
                ),
            )
            self.sqlite_conn.commit()
        except Exception as e:
            logger.error(f"Failed to record episode: {e}")

    async def record_incident(self, run_id: str, incident: Dict[str, Any]) -> None:
        """Record incident to SQLite"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sqlite_conn.execute(
                    """
                    INSERT INTO incidents (run_id, timestamp, incident_type, severity, details_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        incident.get("timestamp"),
                        incident.get("incident_type"),
                        incident.get("severity"),
                        json.dumps(incident.get("details", {})),
                    ),
                ),
            )
            self.sqlite_conn.commit()
        except Exception as e:
            logger.error(f"Failed to record incident: {e}")
