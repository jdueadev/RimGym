"""
Protobuf message parsers for Phase V state data.

Converts raw protobuf messages to typed Python data models.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for protobuf imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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

logger = logging.getLogger(__name__)


def parse_terrain_cell(proto_cell) -> TerrainCell:
    """Convert protobuf TerrainCell to Python model."""
    return TerrainCell(
        x=proto_cell.x,
        y=proto_cell.y,
        terrain_type=proto_cell.terrain_type,
        fertility=proto_cell.fertility,
        traversal_cost=proto_cell.traversal_cost,
        can_build=proto_cell.can_build,
    )


def parse_building(proto_building) -> Building:
    """Convert protobuf Building to Python model."""
    return Building(
        thing_id=proto_building.thing_id,
        building_type=proto_building.building_type,
        x=proto_building.x,
        y=proto_building.y,
        health_percent=proto_building.health_percent,
        is_damaged=proto_building.is_damaged,
        owner_id=proto_building.owner_id if proto_building.owner_id > 0 else None,
    )


def parse_item(proto_item) -> Item:
    """Convert protobuf Item to Python model."""
    return Item(
        thing_id=proto_item.thing_id,
        item_type=proto_item.item_type,
        x=proto_item.x,
        y=proto_item.y,
        stack_count=proto_item.stack_count,
        quality=proto_item.quality if proto_item.quality else "Normal",
    )


def parse_zone(proto_zone) -> Zone:
    """Convert protobuf Zone to Python model."""
    cells = [(cell.x, cell.y) for cell in proto_zone.cells]
    return Zone(
        zone_id=proto_zone.zone_id,
        zone_type=proto_zone.zone_type,
        cells=cells,
        label=proto_zone.label,
    )


def parse_room(proto_room) -> Room:
    """Convert protobuf Room to Python model."""
    cells = [(cell.x, cell.y) for cell in proto_room.cells]
    return Room(
        room_id=proto_room.room_id,
        cells=cells,
        is_outdoors=proto_room.is_outdoors,
        temperature=proto_room.temperature,
        cleanliness=proto_room.cleanliness,
        impressiveness=proto_room.impressiveness,
        role=proto_room.role,
    )


def parse_map_state(proto_map) -> MapState:
    """Convert protobuf MapState to Python model."""
    return MapState(
        map_size_x=proto_map.map_size_x,
        map_size_z=proto_map.map_size_z,
        terrain=[parse_terrain_cell(cell) for cell in proto_map.terrain],
        buildings=[parse_building(building) for building in proto_map.buildings],
        items=[parse_item(item) for item in proto_map.items],
        zones=[parse_zone(zone) for zone in proto_map.zones],
        rooms=[parse_room(room) for room in proto_map.rooms],
    )


def parse_incident_record(proto_incident) -> IncidentRecord:
    """Convert protobuf IncidentRecord to Python model."""
    return IncidentRecord(
        incident_type=proto_incident.incident_type,
        frame_id=proto_incident.frame_id,
        severity=proto_incident.severity,
        faction_involved=proto_incident.faction_involved,
        target_pawn_ids=list(proto_incident.target_pawn_ids),
    )


def parse_storyteller_info(proto_storyteller) -> StorytellerInfo:
    """Convert protobuf StorytellerInfo to Python model."""
    return StorytellerInfo(
        storyteller_name=proto_storyteller.storyteller_name,
        difficulty=proto_storyteller.difficulty,
    )


def parse_threat_status(proto_threats) -> ThreatStatus:
    """Convert protobuf ThreatStatus to Python model."""
    return ThreatStatus(
        active_raids=proto_threats.active_raids,
        active_fires=proto_threats.active_fires,
        active_mental_breaks=proto_threats.active_mental_breaks,
        total_threat_points=proto_threats.total_threat_points,
    )


def parse_incident_state(proto_incidents) -> IncidentState:
    """Convert protobuf IncidentState to Python model."""
    recent_incidents = [
        parse_incident_record(inc) for inc in proto_incidents.recent_incidents
    ]

    storyteller = None
    if proto_incidents.HasField("storyteller"):
        storyteller = parse_storyteller_info(proto_incidents.storyteller)

    threats = None
    if proto_incidents.HasField("threats"):
        threats = parse_threat_status(proto_incidents.threats)

    return IncidentState(
        recent_incidents=recent_incidents,
        storyteller=storyteller,
        threats=threats,
    )


def parse_faction(proto_faction) -> Faction:
    """Convert protobuf Faction to Python model."""
    return Faction(
        faction_id=proto_faction.faction_id,
        name=proto_faction.name,
        relation=proto_faction.relation,
        goodwill=proto_faction.goodwill,
    )


def parse_settlement(proto_settlement) -> Settlement:
    """Convert protobuf Settlement to Python model."""
    return Settlement(
        settlement_id=proto_settlement.settlement_id,
        name=proto_settlement.name,
        faction_id=proto_settlement.faction_id,
        tile_id=proto_settlement.tile_id,
        x=proto_settlement.x,
        y=proto_settlement.y,
    )


def parse_caravan(proto_caravan) -> Caravan:
    """Convert protobuf Caravan to Python model."""
    return Caravan(
        caravan_id=proto_caravan.caravan_id,
        tile_id=proto_caravan.tile_id,
        x=proto_caravan.x,
        y=proto_caravan.y,
        pawn_ids=list(proto_caravan.pawn_ids),
        is_player_controlled=proto_caravan.is_player_controlled,
    )


def parse_world_state(proto_world) -> WorldState:
    """Convert protobuf WorldState to Python model."""
    return WorldState(
        factions=[parse_faction(faction) for faction in proto_world.factions],
        settlements=[
            parse_settlement(settlement) for settlement in proto_world.settlements
        ],
        caravans=[parse_caravan(caravan) for caravan in proto_world.caravans],
    )


def parse_colonist_basic(proto_entity) -> ColonistBasic:
    """Convert protobuf Entity to basic colonist data."""
    return ColonistBasic(
        pawn_id=proto_entity.pawn_id,
        name=proto_entity.name,
        health=proto_entity.health,
        x=proto_entity.position.x if proto_entity.HasField("position") else 0.0,
        y=proto_entity.position.z if proto_entity.HasField("position") else 0.0,
        current_job=proto_entity.current_job,
    )


def parse_rich_state_message(proto_msg) -> RichGameState:
    """
    Convert protobuf RichStateMessage to Python RichGameState model.

    Handles both legacy StateMessage fields and new Phase V fields.

    Args:
        proto_msg: Protobuf RichStateMessage

    Returns:
        Parsed RichGameState with all available data
    """
    # Parse basic colonist data
    colonists = [parse_colonist_basic(entity) for entity in proto_msg.entities]

    # Parse Phase V data (may be None if server doesn't support Phase V)
    map_state = None
    if proto_msg.HasField("map"):
        try:
            map_state = parse_map_state(proto_msg.map)
            logger.debug(
                f"Parsed map state: {len(map_state.buildings)} buildings, "
                f"{len(map_state.items)} items"
            )
        except Exception as e:
            logger.error(f"Failed to parse map state: {e}")

    incident_state = None
    if proto_msg.HasField("incidents"):
        try:
            incident_state = parse_incident_state(proto_msg.incidents)
            logger.debug(
                f"Parsed incident state: {len(incident_state.recent_incidents)} incidents"
            )
        except Exception as e:
            logger.error(f"Failed to parse incident state: {e}")

    world_state = None
    if proto_msg.HasField("world"):
        try:
            world_state = parse_world_state(proto_msg.world)
            logger.debug(
                f"Parsed world state: {len(world_state.factions)} factions, "
                f"{len(world_state.settlements)} settlements"
            )
        except Exception as e:
            logger.error(f"Failed to parse world state: {e}")

    # Detect if Phase V data is present
    is_phase_v = any([map_state, incident_state, world_state])

    return RichGameState(
        frame_id=proto_msg.frame_id,
        tick=proto_msg.tick,
        timestamp_ms=proto_msg.timestamp_ms,
        colonists=colonists,
        map_state=map_state,
        incident_state=incident_state,
        world_state=world_state,
        is_phase_v=is_phase_v,
    )
