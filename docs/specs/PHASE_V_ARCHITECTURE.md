# Phase V: RIMAPI Full Integration - Complete Game Observability

## Overview

Phase V extends the RimWorld ML Bridge with complete game observability by integrating data extraction logic from the RIMAPI project. This provides machine learning agents with high-fidelity access to all game state, enabling advanced strategic reasoning and long-term planning.

## Architecture

### Data Flow

```
RimWorld Game State
      ↓
Services Layer (ColonistService, MapService, IncidentService)
      ↓
DTOs (Data Transfer Objects)
      ↓
Protobuf Adapters (MapAdapter, IncidentAdapter, WorldAdapter)
      ↓
RichStateMessage (Protobuf)
      ↓
TCP Network
      ↓
Python Client
      ↓
RichGameState (Typed Python Models)
      ↓
ML Agent
```

### Components

#### 1. Services Layer (C#)

Located in `RimworldMLBridge/Services/`:

- **ColonistService**: Extracts colonist data (health, needs, skills, relationships)
- **MapService**: Extracts map data (terrain, buildings, items, zones, rooms)
- **IncidentService**: Tracks game events, storyteller state, active threats

#### 2. DTOs (Data Transfer Objects)

Located in `RimworldMLBridge/DTOs/`:

- **ColonistDTO**: Colonist state (ported from RIMAPI)
- **MapDTO**: Map state with terrain, buildings, items
- **IncidentsDTO**: Event history and game conditions
- **WorldStateDTO**: World-level data (factions, settlements, caravans)

#### 3. Protobuf Adapters

Located in `RimworldMLBridge/Adapters/`:

- **ColonistAdapter**: Converts ColonistDTO → ColonistState protobuf
- **MapAdapter**: Converts MapDTO → MapState protobuf
- **IncidentAdapter**: Converts IncidentsDTO → IncidentState protobuf
- **WorldAdapter**: Converts WorldStateDTO → WorldState protobuf

Each adapter performs efficient DTO→Protobuf conversion with <1ms target latency.

#### 4. Protobuf Schema

Located in `Protos/mlbridge.proto`:

Key message types:

- **RichStateMessage**: Root message containing all game state
- **MapState**: Terrain, buildings, items, zones, rooms
- **IncidentState**: Event history, storyteller, active threats
- **WorldState**: Factions, settlements, caravans

Complete with 10+ enums (TerrainType, BuildingType, IncidentType, FactionRelation, etc.)

#### 5. Python Client

Located in `python/client/`:

- **state_models.py**: Typed Python dataclasses for game state
- **parsers.py**: Converts protobuf messages to Python models
- **connection.py**: TCP connection with RichStateMessage support
- **spectator_client.py**: High-level client API returning RichGameState

## Data Structures

### MapState

Provides complete map observability:

- **Terrain**: Grid of terrain cells (type, fertility, traversal cost)
- **Buildings**: All structures (walls, doors, beds, workbenches) with health/ownership
- **Items**: All items on map (resources, weapons, apparel) with quality/stack count
- **Zones**: Player-defined zones (stockpiles, growing zones, dumping areas)
- **Rooms**: Detected rooms with temperature, cleanliness, impressiveness, role

Example:

```python
state = client.get_state()
if state.map_state:
    print(f"Map: {state.map_state.building_count} buildings")
    print(f"     {state.map_state.item_count} items")
    
    # Find all damaged buildings
    for building in state.map_state.buildings:
        if building.is_damaged:
            print(f"{building.building_type} at ({building.x}, {building.y}): {building.health_percent}% health")
```

### IncidentState

Tracks game events and difficulty:

- **Recent Incidents**: History of events (raids, fires, eclipses, traders)
- **Storyteller Info**: Current storyteller and difficulty setting
- **Threat Status**: Active raids, fires, mental breaks, threat points

Example:

```python
if state.incident_state:
    # Check for active threats
    threats = state.incident_state.threats
    if threats.active_raids > 0:
        print(f"⚠ {threats.active_raids} raids in progress!")
    
    # Analyze incident history
    recent_raids = state.incident_state.get_recent_raids()
    print(f"Raid frequency: {len(recent_raids)} in recent history")
```

### WorldState

Provides world-level context:

- **Factions**: All factions with relations and goodwill scores
- **Settlements**: All known settlements with locations
- **Caravans**: Player caravans with positions and members

Example:

```python
if state.world_state:
    # Check faction relations
    hostile_factions = state.world_state.get_hostile_factions()
    allied_factions = state.world_state.get_allied_factions()
    
    print(f"Hostile: {len(hostile_factions)}, Allied: {len(allied_factions)}")
    
    # Find nearest hostile settlement
    for settlement in state.world_state.settlements:
        faction = state.world_state.get_faction_by_id(settlement.faction_id)
        if faction and faction.relation == "Hostile":
            print(f"Hostile settlement: {settlement.name} at ({settlement.x}, {settlement.y})")
```

## Performance

### Target Metrics

- **Total Extraction Time**: <5ms per full state query
- **Serialization**: <1ms for protobuf serialization
- **Network Transfer**: Depends on data size (typical: 10-50KB)
- **Python Parsing**: <1ms for protobuf→Python model conversion

### Profiling

The C# server includes built-in performance profiling:

```csharp
// Automatic profiling enabled in TcpProtobufServer
// Logs stats every 100 frames:
// [MLBridge:Performance] Map Extraction: 2ms (150 buildings, 300 items)
//                        Incident Extraction: 1ms (50 incidents)
//                        World Extraction: 1ms (15 factions, 40 settlements)
//                        Total Extraction: 4ms
```

Python performance testing:

```bash
# Run performance test
python python/performance_test_phase5.py

# Run stress test (requires large colony)
python python/performance_test_phase5.py --stress
```

### Optimization Strategies

If extraction time exceeds targets:

1. **Caching**: Cache rarely-changing data (terrain, factions) between queries
2. **Sampling**: Reduce detail level (e.g., send every 2nd terrain cell)
3. **Delta Compression**: Only send changed data in async mode (Task 6)
4. **Lazy Evaluation**: Only extract requested data fields
5. **Spatial Partitioning**: Only extract entities near colonists

## Usage Examples

### Basic State Query

```python
from client import ClientConfig, SpectatorClient

config = ClientConfig(host="localhost", port=50051, inference_mode=True)

with SpectatorClient(config) as client:
    client.wait_ready(timeout=10.0)
    
    state = client.get_state()
    
    if state.is_phase_v:
        print("Phase V Data Available!")
        print(state.summary())
    else:
        print("Server does not support Phase V")
```

### Full Observability Demo

See `python/examples/phase5_full_observability.py` for comprehensive example showing:

- Colonist data access
- Map exploration (buildings, items, zones, rooms)
- Incident history and threat monitoring
- World state and faction relations
- Continuous monitoring with performance metrics

Run with:

```bash
uv run python python/examples/phase5_full_observability.py
```

### Strategic Decision Making

Example: Raid defense strategy

```python
state = client.get_state()

# Check for active threats
if state.incident_state and state.incident_state.threats:
    threats = state.incident_state.threats
    
    if threats.active_raids > 0:
        # Get defensive positions (walls, turrets)
        defensive_buildings = [
            b for b in state.map_state.buildings 
            if b.building_type in ["Turret_MiniTurret", "Sandbags", "Barricade"]
        ]
        
        # Check weapon stockpile
        weapons = [
            i for i in state.map_state.items 
            if "Rifle" in i.item_type or "Gun" in i.item_type
        ]
        
        print(f"Defenses: {len(defensive_buildings)} structures, {len(weapons)} weapons")
        
        # Agent decides: fight or flight?
        if len(defensive_buildings) < 5 or len(weapons) < len(state.colonists):
            print("Weak defenses - consider retreat to safe room")
        else:
            print("Strong defenses - prepare to engage")
```

## API Reference

### Python Client

#### RichGameState

Main state object returned by `client.get_state()`:

**Properties:**

- `frame_id`: Current game tick
- `tick`: Game tick (same as frame_id)
- `timestamp_ms`: Server timestamp
- `colonists`: List of ColonistBasic objects
- `map_state`: MapState object (or None)
- `incident_state`: IncidentState object (or None)
- `world_state`: WorldState object (or None)
- `is_phase_v`: True if Phase V data is present

**Methods:**

- `summary()`: Generate human-readable summary string
- `colonist_count`: Property returning total colonists
- `has_map_data`: Property checking if map data is available
- `has_incident_data`: Property checking if incident data is available
- `has_world_data`: Property checking if world data is available

#### MapState

**Properties:**

- `map_size_x`, `map_size_z`: Map dimensions
- `terrain`: List of TerrainCell objects
- `buildings`: List of Building objects
- `items`: List of Item objects
- `zones`: List of Zone objects
- `rooms`: List of Room objects

**Methods:**

- `building_count`: Property returning total buildings
- `item_count`: Property returning total items
- `get_building_by_id(thing_id)`: Find building by ThingID
- `get_buildings_at(x, y)`: Get all buildings at coordinates

#### IncidentState

**Properties:**

- `recent_incidents`: List of IncidentRecord objects
- `storyteller`: StorytellerInfo object
- `threats`: ThreatStatus object

**Methods:**

- `incident_count`: Property returning total incidents
- `get_incidents_by_type(incident_type)`: Filter by type
- `get_recent_raids()`: Get recent raid incidents

#### WorldState

**Properties:**

- `factions`: List of Faction objects
- `settlements`: List of Settlement objects
- `caravans`: List of Caravan objects

**Methods:**

- `faction_count`, `settlement_count`: Property counts
- `get_faction_by_id(faction_id)`: Find faction by ID
- `get_hostile_factions()`: Get all hostile factions
- `get_allied_factions()`: Get all allied factions

### C# Server

#### TcpProtobufServer.PopulatePhaseVState()

Called automatically during QUERY_STATE command handling.

**Parameters:**

- `state`: RichStateMessage to populate
- `mapId`: Current map ID

**Behavior:**

1. Extracts map data via MapService
2. Extracts incident data via IncidentService
3. Extracts world data from Find.World
4. Converts DTOs to protobuf via adapters
5. Populates state.Map, state.Incidents, state.World fields

**Performance:**

- Automatically profiled with PerformanceProfiler
- Logs stats every 100 frames

## Migration Guide

### From Legacy StateMessage

If your code uses the old `StateMessage`:

**Before (Phase IV):**

```python
state = client.get_state()  # Returns StateMessage
colonists = state.entities  # List of Entity protobuf messages
for colonist in colonists:
    print(f"{colonist.name}: {colonist.health}")
```

**After (Phase V):**

```python
state = client.get_state()  # Returns RichGameState
colonists = state.colonists  # List of ColonistBasic objects
for colonist in colonists:
    print(f"{colonist.name}: {colonist.health}")

# New Phase V data:
if state.map_state:
    print(f"Buildings: {state.map_state.building_count}")
```

**Backward Compatibility:**

- The server still supports legacy clients
- If server doesn't support Phase V, `is_phase_v` will be False
- Phase V fields (map_state, incident_state, world_state) will be None

## Troubleshooting

### "Phase V data not present"

**Cause:** Server mod is not Phase V compatible (using older version)

**Solution:**

1. Rebuild C# mod with Phase V code
2. Ensure DLL is copied to `1.6/Assemblies/`
3. Restart RimWorld
4. Check RimWorld log for "[MLBridge] Phase V state: X buildings..."

### "Extraction time exceeds 10ms"

**Cause:** Large colony with many buildings/items

**Solution:**

1. Run performance profiler: `python performance_test_phase5.py --stress`
2. Check C# logs for per-component timing
3. Consider optimizations:
   - Implement Task 6 (Delta Compression)
   - Add caching for static data
   - Reduce terrain detail (sample every 2nd cell)

### "Python import error for state_models"

**Cause:** Python client package not installed

**Solution:**

```bash
cd python
uv sync
```

## Future Enhancements

### Task 6: Delta Compression (Not Yet Implemented)

Implement change tracking to only send modified data in async mode:

- Add dirty flags to MapService for terrain/buildings/items
- Only populate changed entities when `is_delta=true`
- Reduces network bandwidth for large colonies
- Target: 90% reduction in data transfer for steady-state

### Potential Features

1. **Selective Data Loading**: Client specifies which fields to populate
2. **Spatial Filtering**: Only extract entities within radius of colonists
3. **Temporal Sampling**: Reduce update frequency for slow-changing data
4. **Compression**: Use gzip/lz4 compression for large state messages
5. **Caching Layer**: Redis cache for frequently accessed static data

## References

- **RIMAPI Project**: <https://github.com/RimWorldML/RIMAPI> (data extraction patterns)
- **Protocol Buffers**: <https://protobuf.dev/> (serialization format)
- **RimWorld Modding**: <https://rimworldwiki.com/wiki/Modding_Tutorials>
- **Phase IV Architecture**: See `PHASE_IV_ARCHITECTURE.md`
- **Original Architecture**: See `ARCHITECTURE.md`

## Change Log

### Phase V.1 (2025-01)

- ✅ Extended protobuf schema (+300 lines)
- ✅ Created MapAdapter, IncidentAdapter, WorldAdapter (712 lines)
- ✅ Integrated RIMAPI Services
- ✅ Added Python state models and parsers (580 lines)
- ✅ Created phase5_full_observability.py example
- ✅ Added performance profiling (PerformanceProfiler.cs)
- ✅ Created performance testing suite

### Planned (Phase V.2)

- ⏳ Task 6: Delta Compression implementation
- ⏳ Gym environment observation space extension
- ⏳ Advanced examples (strategic reasoning, multi-agent coordination)
- ⏳ Benchmark suite for large colony performance
