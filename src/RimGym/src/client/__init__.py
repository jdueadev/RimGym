"""RimGym Python client package.

Provides a triple-threaded client for autonomous RL agent interaction with RimWorld,
connecting to the RimTCP mod via TCP + Protocol Buffers.
"""

from .actor import ActorThread
from .connection import ConnectionManager
from .inference import InferenceThread
from .listener import EventDetectionConfig, ListenerThread
from .metrics import MetricsCollector, PerformanceMetrics
from .parsers import parse_rich_state_message
from .queues import ActionQueue, EventQueue, StateQueue
from .spectator_client import ClientConfig, ClientState, SpectatorClient
from .state_models import (
    Building,
    Caravan,
    ColonistBasic,
    Faction,
    IncidentRecord,
    IncidentState,
    Item,
    MapState,
    RichGameState,
    Room,
    Settlement,
    StorytellerInfo,
    TerrainCell,
    ThreatStatus,
    WorldState,
    Zone,
)

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
    "ActorThread",
    "RichGameState",
    "ColonistBasic",
    "MapState",
    "TerrainCell",
    "Building",
    "Item",
    "Zone",
    "Room",
    "IncidentState",
    "IncidentRecord",
    "StorytellerInfo",
    "ThreatStatus",
    "WorldState",
    "Faction",
    "Settlement",
    "Caravan",
    "parse_rich_state_message",
]

__version__ = "0.5.0"
