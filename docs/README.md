# RimGym Documentation

## Getting Started

- [README.md](../README.md) - Project Overview
- [Installation Guide](guides/installation.md) - Detailed setup instructions
- [Docker Quick Start](../docs/docker/QUICKSTART.md) - 60-second Docker testing setup ⚡
- [Docker Troubleshooting](../docs/docker/TROUBLESHOOTING.md) - Common Docker issues and solutions

## Components

- [RimTCP (Mod)](../src/RimTCP/README.md) - C# Mod Documentation
- [RimGym (Python)](../src/RimGym/README.md) - Python Client & Environment Documentation
- [RimStats (Dashboard)](../src/RimStats/README.md) - Dashboard Documentation

## Technical Specifications

- [Architecture Overview](specs/ARCHITECTURE.md) - Deep RL theoretical framework and roadmap
- [Real-Time Architecture](specs/REAL_TIME_ARCHITECTURE_UPDATE.md) - Current implementation design with Hybrid Valve

## Implementation Details

- [TCP + Protobuf Implementation](implementation/TCP_PROTOBUF_IMPLEMENTATION.md) - Current protocol details
- [Phase IV.7: Docker Integration](implementation/PHASE_IV_7_DOCKER_INTEGRATION.md) - Docker testing environment ✅
- [Docker Lessons Learned](implementation/DOCKER_LESSONS_LEARNED.md) - Debugging journey and insights
- [Native DLL Fix](implementation/NATIVE_DLL_FIX.md) - Why we can't use gRPC
- [gRPC Migration History](implementation/GRPC_MIGRATION.md) - Historical reference
- [Implementation Summary](implementation/IMPLEMENTATION_SUMMARY.md) - Phase I recap
- [Phase IV.3 Summary](implementation/PHASE_IV_3_COMPLETION_SUMMARY.md) - Hybrid Valve implementation

## Development

- [Memory Bank](../memory-bank/) - Project context and progress tracking
- [Contributing](../CONTRIBUTING.md) - How to contribute

## API Reference

- [Protobuf Schema](../src/shared/Protos/mlbridge.proto) - Protocol definition
