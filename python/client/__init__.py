"""
RimWorld ML Bridge - Python Client Package

Provides a triple-threaded client for autonomous RL agent interaction with RimWorld.
"""

from .connection import ConnectionManager
from .inference import InferenceThread
from .listener import EventDetectionConfig, ListenerThread
from .metrics import MetricsCollector, PerformanceMetrics
from .queues import ActionQueue, EventQueue, StateQueue
from .spectator_client import ClientConfig, ClientState, SpectatorClient

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
    "ListenerThread",
    "EventDetectionConfig",
    "InferenceThread",
]

__version__ = "0.3.0"
