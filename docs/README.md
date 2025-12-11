# RimGym Documentation

## Getting Started

- [Installation Guide](guides/installation.md) - Detailed setup instructions
- [Docker Quick Start](docker/QUICKSTART.md) - 60-second Docker testing setup ⚡
- [Docker Troubleshooting](docker/TROUBLESHOOTING.md) - Common Docker issues and solutions

## Components

- [RimTCP (Mod)](../src/RimTCP/README.md) - C# Mod Documentation
- [RimGym (Python)](../src/RimGym/README.md) - Python Client & Environment Documentation
- [RimStats (Dashboard)](../src/RimStats/README.md) - Dashboard Documentation

## Technical Specifications

- [Architecture Overview](specs/ARCHITECTURE.md) - Deep RL theoretical framework and roadmap
- [Real-Time Architecture](specs/REAL_TIME_ARCHITECTURE_UPDATE.md) - Hybrid Valve design
- [Phase IV Architecture](specs/PHASE_IV_ARCHITECTURE.md) - Python client architecture
- [Phase V Architecture](specs/PHASE_V_ARCHITECTURE.md) - Full observability design
- [Dashboard Architecture](specs/DASHBOARD_ARCHITECTURE.md) - RimStats design

## Implementation Details

- [TCP + Protobuf Implementation](implementation/TCP_PROTOBUF_IMPLEMENTATION.md) - Protocol details
- [Native DLL Fix](implementation/NATIVE_DLL_FIX.md) - Why we can't use gRPC
- [Docker Lessons Learned](implementation/DOCKER_LESSONS_LEARNED.md) - Debugging insights

## Development

- [Memory Bank](memory-bank/) - Project context and progress tracking
- [Contributing](../CONTRIBUTING.md) - How to contribute
- [Changelog](CHANGELOG.md) - Version history

## API Reference

- [Protobuf Schema](../src/shared/Protos/rimgym.proto) - Protocol definition
- [Python API](api/python/overview.md) - Python client API reference

## Archive

Historical documentation and phase completion summaries are in [archive/](archive/).
