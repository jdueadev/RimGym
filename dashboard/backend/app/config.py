"""Application configuration"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Storage
    redis_url: str = "redis://localhost:6379/0"
    sqlite_path: str = "./data/dashboard.db"

    # Data retention
    redis_ttl_days: int = 7
    sqlite_retention_days: int = 30
    state_buffer_size: int = 1000

    # Performance
    poll_interval_ms: int = 100
    websocket_update_hz: int = 2
    max_concurrent_runs: int = 10
    sqlite_worker_threads: int = 4

    # Auto-discovery
    enable_auto_discovery: bool = True
    docker_network: str = "rimworld_network"
    health_check_interval_s: int = 10
    max_reconnect_attempts: int = 5
    reconnect_backoff_base: int = 2

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
