"""
RimWorld ML Bridge - Python Client Package

Provides a triple-threaded client for autonomous RL agent interaction with RimWorld.
"""

from .connection import ConnectionManager
from .spectator_client import SpectatorClient, ClientConfig, ClientState
from .queues import StateQueue, EventQueue, ActionQueue
from .metrics import MetricsCollector, PerformanceMetrics

__all__ = [
    "ConnectionManager",
    "SpectatorClient",
    "ClientConfig",
    "ClientState",
    "StateQueue",
    "EventQueue",
    "ActionQueue",
    "MetricsCollector",
    "PerformanceMetrics",
]

__version__ = "0.3.0"
