"""
Configuration constants for RimWorld ML Bridge Python client.

This module provides centralized configuration values for the client library.
All values can be overridden via environment variables with the MLBRIDGE_ prefix.
"""

import os
from dataclasses import dataclass


# Network Configuration
DEFAULT_HOST = os.environ.get("MLBRIDGE_HOST", "localhost")
DEFAULT_PORT = int(os.environ.get("MLBRIDGE_PORT", "50051"))

# Connection Settings
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get("MLBRIDGE_TIMEOUT", "5.0"))
HEARTBEAT_INTERVAL_SECONDS = int(os.environ.get("MLBRIDGE_HEARTBEAT_INTERVAL", "30"))
MAX_CONNECTION_ERRORS = int(os.environ.get("MLBRIDGE_MAX_ERRORS", "10"))
RECONNECT_DELAY_SECONDS = float(os.environ.get("MLBRIDGE_RECONNECT_DELAY", "1.0"))
MAX_RECONNECT_ATTEMPTS = int(os.environ.get("MLBRIDGE_MAX_RECONNECT", "5"))

# Protocol Settings
LENGTH_PREFIX_SIZE = 4  # bytes (big-endian int32)
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# Game Tick Settings
TICKS_PER_SECOND = 60  # RimWorld runs at 60 ticks/second at normal speed
DEFAULT_TICKS_PER_STEP = 60  # Default step duration (1 second game time)

# Queue Settings
DEFAULT_QUEUE_SIZE = 100
STATE_QUEUE_SIZE = int(os.environ.get("MLBRIDGE_STATE_QUEUE_SIZE", "10"))
EVENT_QUEUE_SIZE = int(os.environ.get("MLBRIDGE_EVENT_QUEUE_SIZE", "100"))
ACTION_QUEUE_SIZE = int(os.environ.get("MLBRIDGE_ACTION_QUEUE_SIZE", "50"))

# Thread Settings
THREAD_POLL_INTERVAL_SECONDS = 0.1
SHUTDOWN_TIMEOUT_SECONDS = 5.0

# Logging
LOG_PREFIX = "[MLBridge]"


@dataclass
class ClientConfigDefaults:
    """Default configuration values for SpectatorClient."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    heartbeat_interval: int = HEARTBEAT_INTERVAL_SECONDS
    max_errors: int = MAX_CONNECTION_ERRORS
    reconnect_delay: float = RECONNECT_DELAY_SECONDS
    max_reconnect_attempts: int = MAX_RECONNECT_ATTEMPTS
    state_queue_size: int = STATE_QUEUE_SIZE
    event_queue_size: int = EVENT_QUEUE_SIZE
    action_queue_size: int = ACTION_QUEUE_SIZE


# Version
VERSION = "0.5.0"
