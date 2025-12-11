# Services Directory

This directory contains data extraction services ported from the RIMAPI project.

## Purpose

Provide high-fidelity, robust data extraction from RimWorld game objects without coupling to HTTP/JSON layers. These services act as the "data layer" for RimTCP, converting complex RimWorld objects into structured DTOs.

## Architecture Pattern

```
RimWorld Game Objects (Pawn, Map, Thing, etc.)
    ↓
Services (Extract data with null checks, error handling)
    ↓
DTOs (Structured C# objects)
    ↓
Adapters (Convert to Protobuf messages)
    ↓
TCP Server (Serialize and send)
```

## Services Overview

### ColonistService

**Status**: Planned (Phase II)

**Responsibilities**:

- Extract pawn stats (health, mood, consciousness)
- Skills and passions
- Needs (food, rest, recreation, etc.)
- Current job and work queue
- Relationships and social state
- Inventory and equipment
- Memory and thoughts

**Key Methods** (Planned):

```csharp
ColonistDTO GetColonistData(Pawn pawn)
List<ColonistDTO> GetAllColonists(Map map)
SkillsDTO GetSkills(Pawn pawn)
NeedsDTO GetNeeds(Pawn pawn)
```

### MapService

**Status**: Planned (Phase II)

**Responsibilities**:

- Terrain grid data (cell types, walkability)
- Weather and temperature
- Natural resources (ore, trees, animals)
- Building and structure data
- Zone definitions
- Threat level and incident tracking

**Key Methods** (Planned):

```csharp
MapDTO GetMapData(Map map)
TerrainGrid GetTerrainGrid(Map map)
WeatherDTO GetWeather(Map map)
List<ThingDTO> GetBuildings(Map map)
```

### ThingService

**Status**: Planned (Phase II)

**Responsibilities**:

- Generic item/entity extraction
- Resource tracking (materials, food, medicine)
- Equipment and weapons
- Corpses and dead things
- Plants and wildlife

**Key Methods** (Planned):

```csharp
ThingDTO GetThingData(Thing thing)
List<ThingDTO> GetAllThings(Map map)
ResourceDTO GetResourceSummary(Map map)
```

### JobService

**Status**: Planned (Phase II)

**Responsibilities**:

- Current job extraction
- Work priorities and assignments
- Job queue state
- Work performance tracking

**Key Methods** (Planned):

```csharp
JobDTO GetCurrentJob(Pawn pawn)
List<JobDTO> GetJobQueue(Pawn pawn)
WorkPrioritiesDTO GetWorkPriorities(Pawn pawn)
```

### IncidentService

**Status**: Planned (Phase II)

**Responsibilities**:

- Active incidents (raids, fires, mental breaks)
- Storyteller state
- Threat detection
- Historical events

**Key Methods** (Planned):

```csharp
List<IncidentDTO> GetActiveIncidents(Map map)
StorytellerStateDTO GetStorytellerState()
ThreatDTO GetCurrentThreats(Map map)
```

### ServiceRegistry

**Status**: Planned (Phase II)

**Purpose**: Centralized service management and dependency injection.

**Responsibilities**:

- Register all services
- Provide service instances
- Handle service lifecycle
- Manage service dependencies

## Implementation Guidelines

### Thread Safety

**Critical**: All service methods MUST be called from Unity's main thread. Services should not maintain long-lived state or caches that could become stale.

```csharp
// GOOD: Stateless, extract and return
public ColonistDTO GetColonistData(Pawn pawn) {
    if (pawn == null) return null;
    // Extract data...
    return dto;
}

// BAD: Maintains state across frames
private Dictionary<int, ColonistDTO> _cache;
```

### Null Safety

Always check for null before accessing RimWorld objects:

```csharp
if (pawn?.health?.summaryHealth == null) {
    Log.Warning("[MLBridge] Pawn health data unavailable");
    return defaultValue;
}
```

### Performance

- Avoid LINQ in hot paths (use foreach loops)
- Don't allocate large collections unnecessarily
- Cache expensive lookups within a single method call only
- Profile methods that exceed 1ms execution time

### Error Handling

```csharp
try {
    // Extraction logic
} catch (Exception e) {
    Log.Error($"[MLBridge] Service error: {e.Message}");
    return null; // or default DTO
}
```

### Logging

Use consistent `[MLBridge]` prefix:

```csharp
Log.Message("[MLBridge] ColonistService extracted 5 colonists");
Log.Warning("[MLBridge] Pawn has no needs subsystem");
Log.Error("[MLBridge] Failed to extract map data: " + e.Message);
```

## Testing Strategy

Each service should have:

1. **Unit Tests**: Mock RimWorld objects, test extraction logic
2. **Integration Tests**: Test against real game save files
3. **Performance Tests**: Ensure <1ms per operation for typical data

## Migration from RIMAPI

When porting services from RIMAPI:

1. Copy service class file
2. Remove HTTP/Controller dependencies
3. Remove JSON serialization attributes
4. Keep DTO classes and extraction logic
5. Update namespace to `RimworldMLBridge.Services`
6. Add to ServiceRegistry
7. Add tests

## Next Steps

1. Create DTO classes in `DTOs/` directory
2. Port ColonistService as first implementation
3. Create unit tests in `RimworldMLBridge.Tests/Services/`
4. Integrate with TcpProtobufServer via Adapters
