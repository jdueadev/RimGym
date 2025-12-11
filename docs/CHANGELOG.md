# Changelog

All notable changes to the RimWorld ML Bridge project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-12-11

### Changed

- Consolidated documentation structure (architecture, API, guides)
- Updated Harmony ID to `com.jmduea.rimworldmlbridge`
- Standardized version numbers across all package files
- Refactored TODOs to documented Phase VI roadmap items

### Added

- `Constants.cs` - Centralized C# configuration constants
- `config.py` - Centralized Python client configuration
- `docs/architecture/README.md` - Consolidated architecture documentation
- IsDrafted, IsDowned, IsDead fields to ColonistDTO
- Metrics collector wiring for InferenceThread and ActorThread
- Settlement count calculation per faction

### Removed

- `GrpcService.cs` - Legacy gRPC service (replaced by TCP)
- `EntityState` protobuf message (deprecated, use `ColonistState`)
- `test_connection.py` - Duplicate gRPC test client
- `mlbridge_pb2_grpc.py` - Unused gRPC Python stubs
- `UnitTest1.cs` - Placeholder test file

### Fixed

- Placeholder author values in documentation
- Missing type annotations in Python client

## [0.4.0] - 2025-12-08

### Added

- **Phase V: Rich State Extraction**
  - MapState: terrain grid, buildings, items, zones, rooms
  - IncidentState: event history, storyteller state, active threats
  - WorldState: factions, settlements, caravans
- MapAdapter, IncidentAdapter, WorldAdapter for protobuf conversion
- state_models.py with typed Python dataclasses
- parsers.py for protobuf → Python model conversion
- Performance profiler (PerformanceProfiler.cs)
- Phase V integration tests

### Changed

- Extended protobuf schema with 10+ new message types
- Enhanced TcpProtobufServer with rich state population
- Updated SpectatorClient with RichGameState support

## [0.3.0] - 2025-11-25

### Added

- **Phase IV: Triple-Threaded Python Client**
  - ListenerThread: Continuous state reception
  - InferenceThread: Executive policy processing
  - ActorThread: Reflex policy reactions
- SpectatorClient with async operation
- EventDetectionConfig for interrupt handling
- MetricsCollector for performance tracking
- Gymnasium environment wrapper (RimWorldEnv)
- Hierarchical policy architecture (Executive/Reflex)

### Changed

- Migrated from blocking to async client architecture
- Added support for dual-mode operation (training/inference)

## [0.2.0] - 2025-11-15

### Added

- **TCP + Protocol Buffers Implementation**
  - TcpProtobufServer.cs - TCP listener with protobuf serialization
  - Length-prefixed message framing
  - Concurrent command/response queues
- Hybrid Valve for training/inference mode switching
- SET_SPEED command for game speed control
- ColonistAdapter for rich colonist data extraction
- ColonistService ported from RIMAPI

### Changed

- Replaced gRPC with raw TCP (Mono runtime compatibility)
- Updated protobuf schema with CommandMessage/StateMessage

### Removed

- Active gRPC code paths (kept GrpcService.cs as reference)

### Fixed

- Native DLL loading issues with RimWorld's Mono runtime
- Thread safety for main thread dispatch

## [0.1.0] - 2025-11-01

### Added

- Initial project structure
- gRPC server implementation (later replaced)
- Basic Harmony patches (Root.Update, TickManager)
- Protobuf schema (mlbridge.proto)
- Python client prototype
- About.xml mod metadata
- README and basic documentation

### Known Issues

- gRPC native DLLs incompatible with RimWorld's Mono runtime
- Resolved in 0.2.0 by switching to TCP+Protobuf

---

## Implementation Phases Summary

| Phase | Version | Focus |
|-------|---------|-------|
| I | 0.1.0 | Initial gRPC prototype |
| II | 0.2.0 | TCP+Protobuf migration, Hybrid Valve |
| III | 0.2.x | Training/Inference mode switching |
| IV | 0.3.0 | Triple-threaded Python client |
| V | 0.4.0 | Rich state extraction (RIMAPI port) |
| VI | 0.5.0+ | Production hardening, action execution |

For detailed implementation notes, see the [docs/implementation/](implementation/) folder.
