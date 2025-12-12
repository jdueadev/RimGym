# Adapters Directory

This directory contains adapter classes that convert DTOs to Protocol Buffer messages.

## Purpose

Provide a clean separation between internal C# data structures (DTOs) and the wire format (Protobuf). This allows:

- Independent evolution of internal and external representations
- Easy testing of serialization logic
- Performance optimization of specific conversions
- Type-safe mapping with compile-time checks

## Architecture Pattern

```
Services → DTOs → Adapters → Protobuf Messages → TCP Wire Format
```

## Adapter Responsibilities

Each adapter:

1. Takes a DTO as input
2. Maps fields to corresponding Protobuf message
3. Handles type conversions (e.g., enum mapping)
4. Performs value transformations (e.g., unit conversions)
5. Returns a populated Protobuf message ready for serialization

## Base Adapter Pattern

```csharp
public abstract class ProtobufAdapter<TDto, TProto>
{
    public abstract TProto ToProtobuf(TDto dto);
    public abstract TDto FromProtobuf(TProto proto); // Optional: for bidirectional
}
```

## Planned Adapters

### ColonistAdapter

**Status**: Planned (Phase II)

**Converts**: `ColonistDTO` → `ColonistState` (Protobuf)

**Responsibilities**:

- Map health, needs, skills to flat Protobuf structure
- Convert RimWorld enums to Protobuf enums
- Serialize inventory and equipment lists
- Handle optional fields gracefully

**Example**:

```csharp
public class ColonistAdapter : ProtobufAdapter<ColonistDTO, ColonistState>
{
    public override ColonistState ToProtobuf(ColonistDTO dto)
    {
        if (dto == null) return null;
        
        return new ColonistState
        {
            ThingId = dto.ThingID,
            Name = dto.Name ?? "",
            Health = dto.Health,
            Mood = dto.Mood,
            Skills = { MapSkills(dto.Skills) },
            Needs = { MapNeeds(dto.Needs) },
            // ...
        };
    }
    
    private IEnumerable<SkillState> MapSkills(Dictionary<SkillDef, int> skills)
    {
        // Convert skills to protobuf format
    }
}
```

### MapAdapter

**Status**: Planned (Phase II)

**Converts**: `MapDTO` → `MapState` (Protobuf)

**Responsibilities**:

- Serialize terrain grid efficiently (consider delta compression)
- Map weather and temperature data
- Convert building/resource lists
- Handle large map sizes (256x256+ cells)

### ThingAdapter

**Status**: Planned (Phase II)

**Converts**: `ThingDTO` → `ThingState` (Protobuf)

**Responsibilities**:

- Generic item/entity serialization
- Handle diverse Thing types (items, pawns, buildings)
- Map quality and condition data
- Serialize position and rotation

### JobAdapter

**Status**: Planned (Phase II)

**Converts**: `JobDTO` → `JobState` (Protobuf)

**Responsibilities**:

- Serialize job definitions and parameters
- Map job targets and locations
- Convert work priorities
- Handle job queue state

### IncidentAdapter

**Status**: Planned (Phase II)

**Converts**: `IncidentDTO` → `IncidentState` (Protobuf)

**Responsibilities**:

- Serialize active incidents
- Map storyteller state
- Convert threat levels
- Handle event timelines

## Implementation Guidelines

### Performance Optimization

**Target**: <1ms for full state serialization

Strategies:

- Use object pooling for frequently created messages
- Avoid LINQ in hot paths
- Pre-allocate collections with known sizes
- Profile with BenchmarkDotNet

```csharp
// GOOD: Pre-allocate and iterate efficiently
var skills = new RepeatedField<SkillState>(dto.Skills.Count);
foreach (var kvp in dto.Skills)
{
    skills.Add(MapSkill(kvp));
}

// BAD: LINQ creates intermediate collections
var skills = dto.Skills.Select(MapSkill).ToList();
```

### Null Safety

Handle null DTOs and missing fields:

```csharp
public ColonistState ToProtobuf(ColonistDTO dto)
{
    if (dto == null) return null;
    
    var state = new ColonistState
    {
        Name = dto.Name ?? "",  // Protobuf strings can't be null
        Health = dto.Health ?? 0f,
    };
    
    // Only add skills if present
    if (dto.Skills != null && dto.Skills.Count > 0)
    {
        state.Skills.AddRange(MapSkills(dto.Skills));
    }
    
    return state;
}
```

### Type Conversions

Map RimWorld enums to Protobuf enums explicitly:

```csharp
private SkillPassion MapPassion(Passion rimworldPassion)
{
    return rimworldPassion switch
    {
        Passion.None => SkillPassion.None,
        Passion.Minor => SkillPassion.Minor,
        Passion.Major => SkillPassion.Major,
        _ => throw new ArgumentException($"Unknown passion: {rimworldPassion}")
    };
}
```

### Testing

Each adapter should have:

1. **Unit Tests**: Test conversion logic with mock DTOs
2. **Round-Trip Tests**: DTO → Protobuf → DTO should be idempotent (when bidirectional)
3. **Performance Tests**: Benchmark serialization time
4. **Null Handling Tests**: Verify graceful handling of missing data

Example test:

```csharp
[Test]
public void ColonistAdapter_ToProtobuf_MapsAllFields()
{
    // Arrange
    var dto = CreateTestColonistDTO();
    var adapter = new ColonistAdapter();
    
    // Act
    var proto = adapter.ToProtobuf(dto);
    
    // Assert
    Assert.AreEqual(dto.ThingID, proto.ThingId);
    Assert.AreEqual(dto.Name, proto.Name);
    Assert.AreEqual(dto.Health, proto.Health, 0.001f);
    // ... more assertions
}
```

### Error Handling

Log errors but don't crash serialization:

```csharp
try
{
    return ToProtobuf(dto);
}
catch (Exception e)
{
    Log.Error($"[RimTCP] Adapter error: {e.Message}");
    return new ColonistState { ThingId = dto?.ThingID ?? 0 };
}
```

## Delta Compression (Future)

For real-time async mode, implement delta compression:

```csharp
public class MapDeltaAdapter
{
    private MapState _previousState;
    
    public MapStateDelta ToProtobufDelta(MapDTO current)
    {
        var delta = new MapStateDelta();
        
        // Only include changed cells
        for (int i = 0; i < current.TerrainGrid.Length; i++)
        {
            if (_previousState == null || current.TerrainGrid[i] != _previousState.TerrainGrid[i])
            {
                delta.ChangedCells.Add(new TerrainCell { Index = i, Type = current.TerrainGrid[i] });
            }
        }
        
        _previousState = current;
        return delta;
    }
}
```

## Integration with TcpProtobufServer

Adapters are called from the main thread during state extraction:

```csharp
// In TcpProtobufServer.cs or GrpcService.cs
var colonistDTOs = _colonistService.GetAllColonists(Find.CurrentMap);
var colonistAdapter = new ColonistAdapter();

var stateMessage = new StateMessage
{
    FrameId = Find.TickManager.TicksGame,
};

foreach (var dto in colonistDTOs)
{
    stateMessage.Colonists.Add(colonistAdapter.ToProtobuf(dto));
}

return stateMessage;
```

## Next Steps

1. Define Protobuf schema extensions in `Protos/mlbridge.proto`
2. Implement `ColonistAdapter` as first adapter
3. Create base `ProtobufAdapter<TDto, TProto>` class
4. Add unit tests
5. Profile serialization performance
6. Document any deviations from 1:1 DTO mapping
