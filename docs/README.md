# RimWorld ML Bridge Documentation

## Getting Started

- [README.md](../README.md) - Quick start guide
- [Installation Guide](guides/installation.md) - Detailed setup instructions
- [Python Client Guide](guides/python-client.md) - Using the client API (Coming Soon)

## Technical Specifications

- [Architecture Overview](specs/ARCHITECTURE.md) - Deep RL theoretical framework and roadmap
- [Real-Time Architecture](specs/REAL_TIME_ARCHITECTURE_UPDATE.md) - Current implementation design with Hybrid Valve

## Implementation Details

- [TCP + Protobuf Implementation](implementation/TCP_PROTOBUF_IMPLEMENTATION.md) - Current protocol details
- [Native DLL Fix](implementation/NATIVE_DLL_FIX.md) - Why we can't use gRPC
- [gRPC Migration History](implementation/GRPC_MIGRATION.md) - Historical reference
- [Implementation Summary](implementation/IMPLEMENTATION_SUMMARY.md) - Phase I recap

## Development

- [Memory Bank](../memory-bank/) - Project context and progress tracking
- [Building from Source](guides/building.md) - Build instructions (Coming Soon)
- [Contributing](CONTRIBUTING.md) - How to contribute (Coming Soon)
- [Troubleshooting](guides/troubleshooting.md) - Common issues and solutions (Coming Soon)

## API Reference

- [Protobuf Schema](../Protos/mlbridge.proto) - Protocol definition
- [C# API](api/csharp.md) - RimWorld mod API reference (Coming Soon)
- [Python API](api/python.md) - Client API reference (Coming Soon)

## Research & Theory

- [RL Environment Design](research/environment-design.md) - State/action space design (Coming Soon)
- [Performance Benchmarks](research/benchmarks.md) - Training throughput metrics (Coming Soon)
- [Case Studies](research/case-studies.md) - Example agents and results (Coming Soon)
