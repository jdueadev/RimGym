# Codebase Structure

## Root Directory Layout
```
RimGym/
├── .github/                    # GitHub config (CI, templates, instructions)
│   ├── copilot-instructions.md # AI coding agent instructions (comprehensive!)
│   ├── workflows/              # CI/CD pipelines
│   └── prompts/                # AI prompt templates
├── docs/                       # Documentation
│   ├── memory-bank/            # Project context for AI (projectbrief, progress, etc.)
│   ├── specs/                  # Architecture documents
│   ├── guides/                 # User guides
│   └── implementation/         # Technical implementation docs
├── scripts/                    # Build and utility scripts
├── src/                        # Source code (all components)
├── tests/                      # C# tests
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container definition
├── mkdocs.yml                  # Documentation site config
└── .editorconfig               # Editor formatting rules
```

## Source Code (`src/`)

### RimTCP - C# RimWorld Mod
```
src/RimTCP/
├── About/About.xml             # Mod metadata
├── 1.6/Assemblies/             # Build output (DLLs)
└── RimTCP/                     # C# source
    ├── RimTCP.cs               # Main mod entry, Harmony init
    ├── TcpProtobufServer.cs    # TCP server, message handling
    ├── TickPatch.cs            # Harmony patches for game tick control
    ├── Constants.cs            # Configuration constants
    ├── Adapters/               # DTO → Protobuf converters
    │   ├── ColonistAdapter.cs
    │   ├── MapAdapter.cs
    │   ├── IncidentAdapter.cs
    │   └── WorldAdapter.cs
    ├── DTOs/                   # Data transfer objects
    │   ├── ColonistDTO.cs
    │   ├── MapDTO.cs
    │   ├── IncidentDTO.cs
    │   └── WorldDTO.cs
    ├── Services/               # Game data extraction
    │   ├── ColonistService.cs
    │   ├── MapService.cs
    │   ├── IncidentService.cs
    │   └── ResourceService.cs
    └── Diagnostics/            # Profiling
        └── PerformanceProfiler.cs
```

### RimGym - Python Client
```
src/RimGym/
├── pyproject.toml              # Python project config
├── conftest.py                 # Pytest config
├── src/
│   ├── client/                 # TCP client components
│   │   ├── connection.py       # ConnectionManager
│   │   ├── spectator_client.py # Main SpectatorClient
│   │   ├── listener.py         # Background listener thread
│   │   ├── actor.py            # Action execution thread
│   │   ├── inference.py        # Inference thread
│   │   ├── queues.py           # Thread-safe queues
│   │   ├── parsers.py          # Protobuf → Python conversion
│   │   └── state_models.py     # Python state dataclasses
│   ├── gym_env/                # Gymnasium environment
│   │   ├── rimworld_env.py     # RimWorldEnv
│   │   ├── spaces.py           # Observation/action spaces
│   │   └── rewards.py          # Reward shaping
│   ├── policies/               # RL policies
│   │   ├── executive.py        # High-level decision making
│   │   └── reflex.py           # Fast reactive responses
│   ├── examples/               # Usage examples
│   │   ├── spectator_demo.py
│   │   └── train_agent.py
│   └── diagnostics/            # Health checks
│       └── check_rimworld_health.py
└── tests/                      # Python tests
    ├── client/                 # Unit tests for client
    ├── gym_env/                # Env tests
    └── integration/            # End-to-end tests
```

### RimStats - Dashboard
```
src/RimStats/
├── docker-compose.yml          # Dashboard stack
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── models.py           # Pydantic models
│   │   ├── routers/            # API endpoints
│   │   ├── services/           # Business logic
│   │   └── storage/            # Redis + SQLite
│   └── Dockerfile
└── frontend/                   # React frontend
    ├── src/
    │   ├── App.tsx             # Main React component
    │   └── index.tsx           # Entry point
    └── Dockerfile
```

### Shared - Protocol Buffers
```
src/shared/
├── Protos/
│   └── rimgym.proto            # Single source of truth for protocol
└── python/
    └── src/
        ├── generate_proto.py   # Proto → Python generator
        └── rimgym_pb2.py       # Generated Python bindings
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | Comprehensive project guide for AI agents |
| `src/shared/Protos/rimgym.proto` | Protocol definition (state, commands, actions) |
| `src/RimTCP/RimTCP/TcpProtobufServer.cs` | Core TCP server and message handling |
| `src/RimTCP/RimTCP/TickPatch.cs` | Harmony patches for Hybrid Valve |
| `src/RimGym/src/client/spectator_client.py` | Main Python client entry point |
| `docs/memory-bank/progress.md` | Project progress tracking |
| `docs/memory-bank/activeContext.md` | Current work focus |
