# System Patterns

## Architecture Overview

### Communication Flow

```
Python RL Agent (TCP Client)  ←→  RimWorld Mod (TCP Server)
   Port 50051, Protobuf              Background Thread → Main Thread
```

### Threading Model (Critical!)

```
┌─────────────────┐
│ Background      │ 1. TCP Listener receives messages
│ Thread          │ 2. Enqueue to ConcurrentQueue<CommandMessage>
│ (TcpProtobufServer) │ 3. Enqueue responses
└─────────────────┘
         ↓ Queue
┌─────────────────┐
│ Main Thread     │ 4. Root_Update_Patch dequeues commands
│ (Unity)         │ 5. Executes on main thread (safe)
│                 │ 6. Returns StateMessage
└─────────────────┘
```

**Rule**: Never access `Current.Game`, `Find.*`, or any Unity objects from background threads!

## Key Design Patterns

### 1. Hybrid Valve Pattern

Dual-mode tick control for training vs inference:

```csharp
// TickManager_DoSingleTick_Patch
public static bool Prefix() {
    if (MlBridgeMod.TrainingMode) {
        // Block tick unless STEP command received
        return MlBridgeMod.StepRequested;
    }
    return true; // Normal flow in inference mode
}
```

### 2. Intent-Based Actions

Semantic commands instead of fragile coordinates:

```protobuf
message ActionIntent {
    enum Type {
        EXECUTE_JOB = 0;
        DRAFT_PAWN = 1;
        SET_PRIORITY = 2;
    }
    Type type = 1;
    int32 pawn_id = 2;
    int32 target_id = 3; // ThingID, not coordinates
    string job_def_name = 4;
}
```

### 3. Server-Side Validation

C# validates before execution:

```csharp
bool ValidateAction(ActionIntent intent) {
    var pawn = Find.Things.GetByThingID(intent.pawn_id);
    if (pawn == null || pawn.Dead) return false;
    
    var target = Find.Things.GetByThingID(intent.target_id);
    if (target == null) return false;
    
    if (!pawn.CanReach(target)) return false;
    
    return true;
}
```

### 4. DTO → Protobuf Adapter Pattern

```csharp
// DTOs (internal C# representation)
class ColonistDTO {
    int ThingID;
    float Health;
    Dictionary<SkillDef, int> Skills;
    List<NeedDTO> Needs;
}

// Adapter converts to Protobuf
class ColonistAdapter {
    ColonistState ToProtobuf(ColonistDTO dto) {
        // Map complex C# objects to flat Protobuf messages
    }
}
```

### 5. Length-Prefixed Framing

```csharp
// Send: [4-byte length][protobuf bytes]
byte[] lengthPrefix = BitConverter.GetBytes(IPAddress.HostToNetworkOrder(data.Length));
await stream.WriteAsync(lengthPrefix);
await stream.WriteAsync(data);

// Receive: Read 4 bytes, then read that many bytes
byte[] lengthBuffer = new byte[4];
await stream.ReadAsync(lengthBuffer);
int length = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(lengthBuffer));
byte[] data = new byte[length];
await stream.ReadAsync(data);
```

## Component Relationships

```text
TcpProtobufServer (Background Thread)
    ↓ enqueues
CommandQueue (Thread-Safe)
    ↓ consumed by
Root_Update_Patch (Main Thread)
    ↓ calls
TcpProtobufServer.ProcessCommand()
    ↓ uses
Services/ (ColonistService, MapService, IncidentService, ResourceService)
    ↓ returns
DTOs/ (ColonistDTO, MapDTO, WorldDTO)
    ↓ mapped by
Adapters/ (ColonistAdapter, MapAdapter, IncidentAdapter, WorldAdapter)
    ↓ serializes to
RichStateMessage (Protobuf)
    ↓ sent by
TcpProtobufServer.SendResponse()
```

## Error Handling Patterns

### Graceful Degradation

```csharp
try {
    var colonists = Find.CurrentMap?.mapPawns?.FreeColonistsSpawned;
    if (colonists == null) {
        Log.Warning("[MLBridge] No colonists available");
        return new StateMessage { frame_id = 0 };
    }
    // Process colonists...
} catch (Exception e) {
    Log.Error($"[MLBridge] State extraction failed: {e}");
    return new StateMessage { error = e.Message };
}
```

### Action Validation

```csharp
if (!ValidateAction(action)) {
    return new ActionResult {
        success = false,
        failure_reason = "Pawn cannot reach target"
    };
}
```

## Performance Patterns

### Avoid Allocations in Hot Paths

```csharp
// BAD: Creates new list every frame
var colonists = Find.CurrentMap.mapPawns.FreeColonistsSpawned.ToList();

// GOOD: Use enumerator directly
foreach (var pawn in Find.CurrentMap.mapPawns.FreeColonistsSpawned) {
    // Process...
}
```

### Cache Expensive Lookups

```csharp
private Dictionary<int, Pawn> _pawnCache = new Dictionary<int, Pawn>();

Pawn GetPawn(int thingID) {
    if (!_pawnCache.TryGetValue(thingID, out var pawn)) {
        pawn = Find.Things.GetByThingID(thingID) as Pawn;
        if (pawn != null) _pawnCache[thingID] = pawn;
    }
    return pawn;
}
```

## Logging Conventions

All logs prefixed with `[RimTCP]` for easy filtering:

```csharp
Log.Message("[RimTCP] TCP+Protobuf server started successfully!");
Log.Warning("[RimTCP] No game loaded, waiting...");
Log.Error("[RimTCP] Command processing failed: " + e.Message);
```
