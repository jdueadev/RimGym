# Active Context

## Current Focus

**Status**: All major development complete. Project is production-ready.

**Version**: 0.5.0

---

## Recent Completions (2025-12-11)

### Dashboard Implementation ✅

Full-stack RimStats dashboard with:

- FastAPI backend + React frontend
- Hybrid Redis + SQLite storage
- Real-time multi-run monitoring
- Docker deployment

### Codebase Cleanup ✅

- Legacy code removed (GrpcService, EntityState)
- Version updated to 0.5.0
- Documentation consolidated
- 148 tests passing

### Production Hardening ✅

- CI/CD pipelines (GitHub Actions)
- MkDocs documentation
- Steam Workshop packaging
- Contributor guides

---

## Next Steps

1. **Public Release**
   - Publish to Steam Workshop
   - Publish Python package to PyPI
   - Announce to RimWorld modding community

2. **Future Enhancements** (Post-Release)
   - Neural network policies
   - Multi-agent coordination
   - Enhanced action validation
   - Performance optimizations

---

## Active Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| DEC-001 | Port RIMAPI services | Proven robustness over building from scratch |
| DEC-002 | Protobuf over JSON | Performance (<1ms vs ~5-10ms) |
| DEC-003 | Raw TCP over gRPC | Native DLL incompatibility with Mono |
| DEC-004 | RichStateMessage for all responses | Unified message format |
| DEC-005 | Hybrid storage (Redis + SQLite) | Real-time + historical data |

---

## Blockers

None currently.

---

## Quick Reference

### Build Commands

```powershell
# C# build
dotnet build src\RimTCP\RimTCP\RimTCP.sln -c Release

# Python tests
uv run pytest src/RimGym/tests/

# Docker dashboard
docker-compose -f src/RimStats/docker-compose.yml up -d
```

### Key Files

- Schema: `src/shared/Protos/rimgym.proto`
- C# Server: `src/RimTCP/RimTCP/TcpProtobufServer.cs`
- Python Client: `src/RimGym/src/client/spectator_client.py`
- Dashboard: `src/RimStats/`
