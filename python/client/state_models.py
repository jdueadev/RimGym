"""
State data models for Phase V - Complete Game Observability.

Provides typed access to map, incident, and world state data from RichStateMessage.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class TerrainCell:
    """Single terrain cell with type and traversal cost."""

    x: int
    y: int
    terrain_type: str  # "Soil", "Sand", "Water", etc.
    fertility: float
    traversal_cost: int
    can_build: bool


@dataclass
class Building:
    """Building/structure on the map."""

    thing_id: int
    building_type: str  # "Wall", "Door", "Bed", "WorkBench", etc.
    x: int
    y: int
    health_percent: float
    is_damaged: bool
    owner_id: Optional[int] = None  # Pawn ID if assigned


@dataclass
class Item:
    """Item on the map (resources, weapons, etc)."""

    thing_id: int
    item_type: str  # "Steel", "Component", "Rifle", etc.
    x: int
    y: int
    stack_count: int
    quality: str = "Normal"  # "Awful", "Poor", "Normal", "Good", "Excellent", "Masterwork", "Legendary"


@dataclass
class Zone:
    """Player-defined zones (stockpiles, growing zones, etc)."""

    zone_id: int
    zone_type: str  # "Stockpile", "Growing", "Dumping", "Animal", etc.
    cells: List[Tuple[int, int]] = field(default_factory=list)  # (x, y) coordinates
    label: str = ""


@dataclass
class Room:
    """Enclosed room detected by game engine."""

    room_id: int
    cells: List[Tuple[int, int]] = field(default_factory=list)
    is_outdoors: bool = False
    temperature: float = 21.0  # Celsius
    cleanliness: float = 0.0
    impressiveness: float = 0.0
    role: str = "Barracks"  # "Barracks", "Hospital", "Kitchen", "Dining", etc.


@dataclass
class MapState:
    """
    Complete map state from Phase V.

    Provides high-fidelity terrain, buildings, items, zones, and rooms data.
    """

    map_size_x: int
    map_size_z: int

    # Terrain (can be large, ~10k cells for 250x250 map)
    terrain: List[TerrainCell] = field(default_factory=list)

    # Buildings (typically 100-500 in mid-game colony)
    buildings: List[Building] = field(default_factory=list)

    # Items (can be large in stockpiles)
    items: List[Item] = field(default_factory=list)

    # Zones (typically 10-50)
    zones: List[Zone] = field(default_factory=list)

    # Rooms (typically 20-100)
    rooms: List[Room] = field(default_factory=list)

    @property
    def building_count(self) -> int:
        """Total number of buildings on map."""
        return len(self.buildings)

    @property
    def item_count(self) -> int:
        """Total number of items on map."""
        return len(self.items)

    def get_building_by_id(self, thing_id: int) -> Optional[Building]:
        """Find building by ThingID."""
        return next((b for b in self.buildings if b.thing_id == thing_id), None)

    def get_buildings_at(self, x: int, y: int) -> List[Building]:
        """Get all buildings at specific coordinates."""
        return [b for b in self.buildings if b.x == x and b.y == y]


@dataclass
class IncidentRecord:
    """Single incident/event that occurred."""

    incident_type: str  # "Raid", "Fire", "Eclipse", "TraderCaravan", etc.
    frame_id: int  # When it occurred
    severity: float  # 0.0 to 1.0
    faction_involved: str = ""
    target_pawn_ids: List[int] = field(default_factory=list)


@dataclass
class StorytellerInfo:
    """Current storyteller configuration."""

    storyteller_name: str  # "Randy", "Cassandra", "Phoebe"
    difficulty: str  # "Peaceful", "Community", "Adventure", "Strive", "Blood and Dust", "Losing is Fun"


@dataclass
class ThreatStatus:
    """Current active threats."""

    active_raids: int
    active_fires: int
    active_mental_breaks: int
    total_threat_points: float


@dataclass
class IncidentState:
    """
    Incident and storyteller state from Phase V.

    Tracks game events, difficulty, and current threats.
    """

    # Recent incident history (last 100 or configurable window)
    recent_incidents: List[IncidentRecord] = field(default_factory=list)

    # Storyteller
    storyteller: Optional[StorytellerInfo] = None

    # Current threats
    threats: Optional[ThreatStatus] = None

    @property
    def incident_count(self) -> int:
        """Total incidents tracked."""
        return len(self.recent_incidents)

    def get_incidents_by_type(self, incident_type: str) -> List[IncidentRecord]:
        """Filter incidents by type."""
        return [i for i in self.recent_incidents if i.incident_type == incident_type]

    def get_recent_raids(self) -> List[IncidentRecord]:
        """Get recent raid incidents."""
        return self.get_incidents_by_type("Raid")


@dataclass
class Faction:
    """World faction information."""

    faction_id: int
    name: str
    relation: str  # "Ally", "Neutral", "Hostile"
    goodwill: float  # -100 to 100


@dataclass
class Settlement:
    """World settlement location."""

    settlement_id: int
    name: str
    faction_id: int
    tile_id: int
    x: float
    y: float


@dataclass
class Caravan:
    """Player caravan traveling on world map."""

    caravan_id: int
    tile_id: int
    x: float
    y: float
    pawn_ids: List[int] = field(default_factory=list)
    is_player_controlled: bool = True


@dataclass
class WorldState:
    """
    World-level state from Phase V.

    Tracks factions, settlements, and caravans on the planet.
    """

    # Factions (typically 10-20)
    factions: List[Faction] = field(default_factory=list)

    # Settlements (can be 50-200 on large maps)
    settlements: List[Settlement] = field(default_factory=list)

    # Caravans (player caravans, typically 0-5)
    caravans: List[Caravan] = field(default_factory=list)

    @property
    def faction_count(self) -> int:
        """Total number of factions."""
        return len(self.factions)

    @property
    def settlement_count(self) -> int:
        """Total number of settlements."""
        return len(self.settlements)

    def get_faction_by_id(self, faction_id: int) -> Optional[Faction]:
        """Find faction by ID."""
        return next((f for f in self.factions if f.faction_id == faction_id), None)

    def get_hostile_factions(self) -> List[Faction]:
        """Get all hostile factions."""
        return [f for f in self.factions if f.relation == "Hostile"]

    def get_allied_factions(self) -> List[Faction]:
        """Get all allied factions."""
        return [f for f in self.factions if f.relation == "Ally"]


@dataclass
class ColonistBasic:
    """Basic colonist data (from original StateMessage)."""

    pawn_id: int
    name: str
    health: float
    x: float
    y: float
    current_job: str = "None"


@dataclass
class RichGameState:
    """
    Complete game state including Phase V observability data.

    This is the primary state object returned by SpectatorClient.get_state()
    when using RichStateMessage.
    """

    # Core data (always present)
    frame_id: int
    tick: int
    timestamp_ms: int

    # Colonists (basic data from original implementation)
    colonists: List[ColonistBasic] = field(default_factory=list)

    # Phase V rich data (may be None if server doesn't support Phase V)
    map_state: Optional[MapState] = None
    incident_state: Optional[IncidentState] = None
    world_state: Optional[WorldState] = None

    # Metadata
    is_phase_v: bool = False  # True if Phase V data is present

    @property
    def colonist_count(self) -> int:
        """Total number of colonists."""
        return len(self.colonists)

    @property
    def has_map_data(self) -> bool:
        """Check if map data is available."""
        return self.map_state is not None

    @property
    def has_incident_data(self) -> bool:
        """Check if incident data is available."""
        return self.incident_state is not None

    @property
    def has_world_data(self) -> bool:
        """Check if world data is available."""
        return self.world_state is not None

    def summary(self) -> str:
        """Generate human-readable summary of game state."""
        lines = [
            f"GameState @ Frame {self.frame_id} (Tick {self.tick})",
            f"  Colonists: {self.colonist_count}",
        ]

        if self.map_state:
            lines.append(
                f"  Buildings: {self.map_state.building_count}, Items: {self.map_state.item_count}"
            )

        if self.incident_state:
            lines.append(f"  Recent Incidents: {self.incident_state.incident_count}")
            if self.incident_state.storyteller:
                lines.append(
                    f"  Storyteller: {self.incident_state.storyteller.storyteller_name} ({self.incident_state.storyteller.difficulty})"
                )

        if self.world_state:
            lines.append(
                f"  Factions: {self.world_state.faction_count}, Settlements: {self.world_state.settlement_count}"
            )

        return "\n".join(lines)
