---
goal: Port RIMAPI Services to RimworldMLBridge for Data Extraction
version: 1.0
date_created: 2025-12-10
last_updated: 2025-12-10
owner: Project Aether Team
status: 'In progress'
tags: ['feature', 'architecture', 'migration', 'phase-ii']
---

# Introduction

![Status: In progress](https://img.shields.io/badge/status-In_progress-yellow)

This implementation plan covers Phase II of the Real-Time Architecture Update: "The Organ Transplant." The goal is to port robust data extraction services from the RIMAPI project (<https://github.com/IlyaChichkov/RIMAPI>) into RimworldMLBridge, replacing HTTP/JSON layers with direct C# DTO returns that can be efficiently serialized to Protobuf format for the TCP bridge.

## 1. Requirements & Constraints

- **REQ-001**: Port core data extraction services from RIMAPI/Source/RIMAPI/RimworldRestApi/Services
- **REQ-002**: Strip HTTP/JSON layers and return raw C# DTOs instead
- **REQ-003**: Create ProtobufAdapter to map C# DTOs to Protobuf StateMessage format
- **REQ-004**: Maintain <1ms serialization time for real-time performance
- **REQ-005**: Implement Intent-Based Action definitions in Protobuf schema
- **REQ-006**: Ensure thread-safety for background TCP operations
- **SEC-001**: Validate all entity references before serialization to prevent null reference exceptions
- **CON-001**: Must work with existing TCP/Protobuf infrastructure
- **CON-002**: Must not break existing TickPatch synchronous mode
- **CON-003**: Must remain compatible with RimWorld 1.6 and .NET Framework 4.8
- **GUD-001**: Follow existing RimworldMLBridge code style and namespace conventions
- **GUD-002**: Keep services modular and independently testable
- **PAT-001**: Use Repository pattern for data access services
- **PAT-002**: Use Adapter pattern for DTO-to-Protobuf conversion

## 2. Implementation Steps

### Implementation Phase 1: Service Analysis & Infrastructure Setup

- GOAL-001: Analyze RIMAPI services and prepare RimworldMLBridge infrastructure

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Clone/download RIMAPI repository and analyze Services directory structure | ✅ | 2025-12-10 |
| TASK-002 | Document all service classes and their responsibilities (ColonistService, MapService, ThingService, etc.) | ✅ | 2025-12-10 |
| TASK-003 | Create Services directory in RimworldMLBridge project | ✅ | 2025-12-10 |
| TASK-004 | Create DTOs directory for data transfer objects | ✅ | 2025-12-10 |
| TASK-005 | Create Adapters directory for ProtobufAdapter classes | | |
| TASK-006 | Update RimworldMLBridge.csproj to include new directories | ✅ | 2025-12-10 |

### Implementation Phase 2: Core Service Migration

- GOAL-002: Port essential data extraction services from RIMAPI

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Port ColonistService.cs - Extract pawn data (stats, needs, skills, health) | ✅ | 2025-12-10 |
| TASK-008 | Port MapService.cs - Extract map terrain, weather, conditions | ✅ | 2025-12-10 |
| TASK-009 | Port ThingService.cs - Extract items, buildings, resources | ✅ | 2025-12-10 |
| TASK-010 | Port JobService.cs - Extract current jobs and work priorities | ✅ | 2025-12-10 |
| TASK-011 | Port IncidentService.cs - Extract events, raids, threats | ✅ | 2025-12-10 |
| TASK-012 | Strip all HTTP/REST/JSON dependencies from ported services | ✅ | 2025-12-10 |

### Implementation Phase 3: DTO Layer Implementation

- GOAL-003: Create clean DTO classes for internal data representation

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | Create ColonistDTO.cs with pawn stats, needs, skills, inventory | ✅ | 2025-12-10 |
| TASK-014 | Create MapDTO.cs with terrain grid, weather, temperature | ✅ | 2025-12-10 |
| TASK-015 | Create ThingDTO.cs with entity properties, position, state | ✅ | 2025-12-10 |
| TASK-016 | Create JobDTO.cs with job type, target, progress, priority | ✅ | 2025-12-10 |
| TASK-017 | Create IncidentDTO.cs with event type, severity, location | ✅ | 2025-12-10 |
| TASK-018 | Create StateDTO.cs as aggregate containing all sub-DTOs | ✅ | 2025-12-10 |

### Implementation Phase 4: Protobuf Schema Extensions

- GOAL-004: Extend mlbridge.proto with Intent-Based Actions and comprehensive state representation

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-019 | Add ColonistState message to mlbridge.proto (stats, needs, skills) | | |
| TASK-020 | Add MapState message to mlbridge.proto (terrain grid, weather) | | |
| TASK-021 | Add ThingState message to mlbridge.proto (entity list with IDs) | | |
| TASK-022 | Add JobState message to mlbridge.proto (active jobs) | | |
| TASK-023 | Add ActionIntent message to mlbridge.proto (intent-based commands) | | |
| TASK-024 | Add ActionResponse message to mlbridge.proto (validation results) | | |
| TASK-025 | Regenerate Protobuf C# code from updated schema | | |

### Implementation Phase 5: ProtobufAdapter Implementation

- GOAL-005: Create efficient mapping layer between DTOs and Protobuf messages

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-026 | Create ProtobufAdapter.cs base class with common serialization logic | | |
| TASK-027 | Implement ColonistAdapter to map ColonistDTO to ColonistState protobuf | | |
| TASK-028 | Implement MapAdapter to map MapDTO to MapState protobuf | | |
| TASK-029 | Implement ThingAdapter to map ThingDTO to ThingState protobuf | | |
| TASK-030 | Implement JobAdapter to map JobDTO to JobState protobuf | | |
| TASK-031 | Implement StateAdapter as main aggregator for complete state | | |
| TASK-032 | Add performance profiling to measure serialization time (<1ms target) | | |

### Implementation Phase 6: TCP Server Integration

- GOAL-006: Integrate services with existing TcpProtobufServer

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-033 | Create ServiceRegistry.cs to manage service instances | | |
| TASK-034 | Update TcpProtobufServer.cs to use ServiceRegistry | | |
| TASK-035 | Implement QUERY_STATE command handler using ported services | | |
| TASK-036 | Implement EXECUTE_ACTION command handler for intent-based actions | | |
| TASK-037 | Add thread-safe action queue for main thread execution | | |
| TASK-038 | Implement validation layer for incoming action intents | | |

### Implementation Phase 7: Delta Compression Implementation

- GOAL-007: Optimize bandwidth with delta compression for real-time mode

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-039 | Create DeltaTracker.cs to store previous state snapshots | | |
| TASK-040 | Implement diff algorithm for map cell changes | | |
| TASK-041 | Implement diff algorithm for entity position/state changes | | |
| TASK-042 | Add frame ID tracking to state messages | | |
| TASK-043 | Create DeltaState protobuf message for compressed updates | | |
| TASK-044 | Add configuration toggle for full vs delta state transmission | | |

### Implementation Phase 8: Testing & Validation

- GOAL-008: Ensure reliability and performance of ported services

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-045 | Create unit tests for each service (ColonistService, MapService, etc.) | | |
| TASK-046 | Create unit tests for DTO-to-Protobuf adapters | | |
| TASK-047 | Create integration test for full state extraction and serialization | | |
| TASK-048 | Benchmark serialization performance (target <1ms) | | |
| TASK-049 | Test with Python SpectatorClient.py to verify end-to-end communication | | |
| TASK-050 | Test action intent validation and execution flow | | |

### Implementation Phase 9: Documentation & Cleanup

- GOAL-009: Document new architecture and clean up temporary artifacts

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-051 | Document service responsibilities in code comments | | |
| TASK-052 | Update REAL_TIME_ARCHITECTURE_UPDATE.md with implementation details | | |
| TASK-053 | Create SERVICE_ARCHITECTURE.md documenting DTO-to-Protobuf flow | | |
| TASK-054 | Add inline documentation for ProtobufAdapter classes | | |
| TASK-055 | Update README.md with new service architecture overview | | |

## 3. Alternatives

- **ALT-001**: Keep HTTP/JSON layer from RIMAPI - Rejected due to performance overhead (JSON serialization ~5-10ms vs Protobuf <1ms)
- **ALT-002**: Use gRPC streaming instead of TCP - Deferred to Phase III as it requires async infrastructure
- **ALT-003**: Implement services from scratch - Rejected to avoid reinventing validated extraction logic
- **ALT-004**: Use MessagePack instead of Protobuf - Rejected due to existing Protobuf infrastructure
- **ALT-005**: Send full state every tick - Rejected due to bandwidth concerns (delta compression more efficient)

## 4. Dependencies

- **DEP-001**: RIMAPI repository (<https://github.com/IlyaChichkov/RIMAPI>) - Source for service logic
- **DEP-002**: Google.Protobuf NuGet package (already installed)
- **DEP-003**: RimWorld 1.6 Assembly-CSharp.dll (already referenced)
- **DEP-004**: 0Harmony.dll for runtime patching (already referenced)
- **DEP-005**: Existing TCP/Protobuf infrastructure from Phase I (complete)
- **DEP-006**: Python SpectatorClient.py for end-to-end testing

## 5. Files

- **FILE-001**: RimworldMLBridge/Services/ColonistService.cs - Pawn data extraction
- **FILE-002**: RimworldMLBridge/Services/MapService.cs - Map data extraction
- **FILE-003**: RimworldMLBridge/Services/ThingService.cs - Entity data extraction
- **FILE-004**: RimworldMLBridge/Services/JobService.cs - Job data extraction
- **FILE-005**: RimworldMLBridge/Services/IncidentService.cs - Event data extraction
- **FILE-006**: RimworldMLBridge/Services/ServiceRegistry.cs - Service lifecycle management
- **FILE-007**: RimworldMLBridge/DTOs/ColonistDTO.cs - Pawn data transfer object
- **FILE-008**: RimworldMLBridge/DTOs/MapDTO.cs - Map data transfer object
- **FILE-009**: RimworldMLBridge/DTOs/ThingDTO.cs - Entity data transfer object
- **FILE-010**: RimworldMLBridge/DTOs/JobDTO.cs - Job data transfer object
- **FILE-011**: RimworldMLBridge/DTOs/IncidentDTO.cs - Event data transfer object
- **FILE-012**: RimworldMLBridge/DTOs/StateDTO.cs - Aggregate state transfer object
- **FILE-013**: RimworldMLBridge/Adapters/ProtobufAdapter.cs - Base adapter class
- **FILE-014**: RimworldMLBridge/Adapters/ColonistAdapter.cs - Colonist DTO-to-Protobuf adapter
- **FILE-015**: RimworldMLBridge/Adapters/MapAdapter.cs - Map DTO-to-Protobuf adapter
- **FILE-016**: RimworldMLBridge/Adapters/ThingAdapter.cs - Thing DTO-to-Protobuf adapter
- **FILE-017**: RimworldMLBridge/Adapters/JobAdapter.cs - Job DTO-to-Protobuf adapter
- **FILE-018**: RimworldMLBridge/Adapters/StateAdapter.cs - State aggregation adapter
- **FILE-019**: RimworldMLBridge/Adapters/DeltaTracker.cs - Delta compression tracker
- **FILE-020**: RimworldMLBridge/TcpProtobufServer.cs - Updated with service integration
- **FILE-021**: Protos/mlbridge.proto - Extended with new state and action messages
- **FILE-022**: Documentation/SERVICE_ARCHITECTURE.md - New architecture documentation

## 6. Testing

- **TEST-001**: Unit test ColonistService.ExtractPawnData() with various pawn states
- **TEST-002**: Unit test MapService.ExtractMapData() with different biomes
- **TEST-003**: Unit test ThingService.ExtractThings() with various entity types
- **TEST-004**: Unit test JobService.ExtractJobs() with active and queued jobs
- **TEST-005**: Unit test IncidentService.ExtractIncidents() with raids and events
- **TEST-006**: Unit test ColonistAdapter serialization performance (<1ms)
- **TEST-007**: Unit test MapAdapter serialization with large map grids
- **TEST-008**: Unit test ThingAdapter with 1000+ entities
- **TEST-009**: Integration test full state extraction → DTO → Protobuf → Python client
- **TEST-010**: Integration test action intent flow: Python → Protobuf → C# → Game
- **TEST-011**: Performance test delta compression bandwidth savings
- **TEST-012**: Stress test with 10 colonists, 500 things, concurrent extraction
- **TEST-013**: Thread safety test with concurrent QUERY_STATE requests
- **TEST-014**: Validation test for malformed action intents

## 7. Risks & Assumptions

- **RISK-001**: RIMAPI code may be tightly coupled to HTTP layer, requiring significant refactoring
- **RISK-002**: Performance target (<1ms serialization) may require optimization iterations
- **RISK-003**: Thread-safety issues when accessing game state from background threads
- **RISK-004**: Protobuf schema changes may break existing Python client compatibility
- **RISK-005**: Delta compression complexity may introduce bugs in state synchronization
- **ASSUMPTION-001**: RIMAPI's data extraction logic is robust and well-tested
- **ASSUMPTION-002**: Existing TCP server infrastructure is stable and performant
- **ASSUMPTION-003**: Python SpectatorClient.py exists and can be used for testing
- **ASSUMPTION-004**: Unity/RimWorld main thread dispatcher pattern will prevent threading issues
- **ASSUMPTION-005**: Delta compression will provide significant bandwidth savings (>50%)

## 8. Related Specifications / Further Reading

- [REAL_TIME_ARCHITECTURE_UPDATE.md](../REAL_TIME_ARCHITECURE_UPDATE.md) - Overall architecture vision
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Original bridge architecture
- [TCP_PROTOBUF_IMPLEMENTATION.md](../TCP_PROTOBUF_IMPLEMENTATION.md) - Phase I TCP implementation
- [RIMAPI GitHub Repository](https://github.com/IlyaChichkov/RIMAPI) - Source for service porting
- [Google Protocol Buffers Documentation](https://protobuf.dev/) - Protobuf schema design
- [RimWorld Modding Wiki](https://rimworldwiki.com/wiki/Modding) - RimWorld API reference
