# Project Folders Structure Blueprint

## 1. Structural Overview

This project is a **Polyglot Monorepo** designed to bridge the RimWorld game engine (C#/.NET) with modern Machine Learning frameworks (Python) and provide real-time visualization (React/FastAPI).

### Organizational Principles

- **Source-Centric**: All source code resides in `src/`, separated by project/domain.
- **Technology-Segregated**: Each sub-project (`RimGym`, `RimStats`, `RimTCP`) maintains its own idiomatic structure appropriate for its language (Python, C#, TypeScript).
- **Shared Contracts**: The `src/shared` directory acts as the source of truth for communication protocols (Protobuf), ensuring type safety across the C#-Python boundary.
- **Documentation-First**: A comprehensive `docs/` directory mirrors the complexity of the codebase, with dedicated sections for architecture, API, and guides.
- **Unified Automation**: The `scripts/` directory contains cross-platform (PowerShell/Bash) scripts for build, deployment, and environment setup.

### Monorepo Organization

The monorepo is organized into three main pillars:

1. **Game Integration (`RimTCP`)**: The "Server" side, running inside RimWorld.
2. **ML Client (`RimGym`)**: The "Client" side, training agents.
3. **Observability (`RimStats`)**: The "Dashboard", monitoring the system.

These pillars are loosely coupled via TCP/Protobuf but tightly integrated in the repository for version consistency.

## 2. Directory Visualization

```text
.
├── docs/                       # Comprehensive project documentation
│   ├── api/                    # API references
│   ├── architecture/           # Architectural decision records and diagrams
│   ├── docker/                 # Containerization guides
│   ├── guides/                 # User and developer guides
│   ├── implementation/         # Implementation details and logs
│   ├── memory-bank/            # AI context and project state
│   └── specs/                  # Technical specifications
├── scripts/                    # Build, deployment, and utility scripts
├── src/                        # Source code roots
│   ├── RimGym/                 # Python RL Environment & Client
│   │   ├── src/                # Python source packages
│   │   │   ├── client/         # TCP client implementation
│   │   │   ├── gym_env/        # Gymnasium environment wrappers
│   │   │   └── policies/       # RL policy implementations
│   │   └── tests/              # Unit tests for RimGym
│   ├── RimStats/               # Dashboard Application
│   │   ├── backend/            # FastAPI Backend
│   │   │   └── app/            # Application logic
│   │   └── frontend/           # React Frontend
│   │       ├── public/         # Static assets
│   │       └── src/            # React components and logic
│   ├── RimTCP/                 # RimWorld C# Mod
│   │   └── RimTCP/             # Mod Source
│   │       ├── Adapters/       # Data adapters (Game -> Proto)
│   │       ├── DTOs/           # Data Transfer Objects
│   │       └── Services/       # Game logic services
│   └── shared/                 # Shared resources
│       ├── Protos/             # Protocol Buffer definitions (.proto)
│       └── python/             # Generated Python code from Protos
└── tests/                      # Global and Integration tests
    └── RimTCP.Tests/           # Unit/Integration tests for C# Mod
```

## 3. Key Directory Analysis

### 3.1. .NET Project Structure (`src/RimTCP`)

- **Solution Organization**: Single solution (`RimTCP.sln`) containing the main mod project and test projects.
- **Layer Organization**:
  - `Adapters/`: Converts internal RimWorld objects to Protobuf messages.
  - `Services/`: Encapsulates game logic and data extraction (e.g., `ColonistService`).
  - `DTOs/`: Intermediate data structures.
- **Output**: Builds to `1.6/Assemblies` to match RimWorld's mod loading structure.

### 3.2. Python Project Structure (`src/RimGym`)

- **Package Layout**: Uses `src/` layout pattern for better packaging isolation.
- **Environment**: Managed via `uv` with `pyproject.toml`.
- **Components**:
  - `gym_env/`: Implements the OpenAI Gymnasium interface.
  - `client/`: Handles low-level TCP communication.

### 3.3. Web Application Structure (`src/RimStats`)

- **Backend (Python/FastAPI)**:
  - `app/`: Contains `main.py`, routers, and models.
  - Uses `docker-compose.yml` for orchestration with Redis/Database.
- **Frontend (React)**:
  - Standard Create React App / Vite structure.
  - `src/`: Components, hooks, and API clients.

## 4. File Placement Patterns

### Configuration Files

- **Project Root**: `docker-compose.yml` (Orchestration), `mkdocs.yml` (Documentation).
- **Python**: `pyproject.toml` in `src/RimGym` and `src/RimStats/backend`.
- **Node**: `package.json`, `tsconfig.json` in `src/RimStats/frontend`.
- **C#**: `.csproj` files in project directories.

### Model/Entity Definitions

- **Shared**: `src/shared/Protos/*.proto` defines the contract.
- **C#**: `src/RimTCP/RimTCP/DTOs/` for internal C# models.
- **Python**: Pydantic models in `src/RimStats/backend/app/models/`.

### Business Logic

- **C#**: `src/RimTCP/RimTCP/Services/` and `TcpProtobufServer.cs`.
- **Python (RL)**: `src/RimGym/src/policies/` and `gym_env/`.
- **Python (Web)**: `src/RimStats/backend/app/routers/`.

## 5. Naming and Organization Conventions

### File Naming

- **C#**: `PascalCase.cs` (e.g., `ColonistService.cs`).
- **Python**: `snake_case.py` (e.g., `colonist_service.py`).
- **React**: `PascalCase.tsx` for components, `camelCase.ts` for utilities.
- **Protobuf**: `snake_case.proto`.

### Folder Naming

- **General**: `PascalCase` for C# folders, `snake_case` for Python packages, `camelCase` or `kebab-case` for Web assets.

### Organizational Patterns

- **Co-location**: Tests are generally co-located with the project (`src/RimGym/tests`) or in a parallel `tests/` directory (`tests/RimTCP.Tests`) depending on language conventions.
- **Feature Encapsulation**: `RimStats` encapsulates both frontend and backend for the dashboard feature.

## 6. Navigation and Development Workflow

### Entry Points

- **Mod**: `src/RimTCP/RimTCP/RimTCP.cs` (Mod initialization).
- **RL Agent**: `src/RimGym/src/examples/` (Example scripts).
- **Dashboard**: `src/RimStats/docker-compose.yml` (Run full stack).

### Common Tasks

- **Adding a new Message**:
  1. Edit `src/shared/Protos/mlbridge.proto`.
  2. Run generation scripts to update C# and Python bindings.
  3. Implement handler in `src/RimTCP`.
  4. Implement client logic in `src/RimGym`.

## 7. Build and Output Organization

### Build Configuration

- **Scripts**: `scripts/` contains `build.sh` and `package-mod.ps1`.
- **Docker**: `Dockerfile` in root and sub-projects for containerized builds.

### Output Structure

- **Mod**: `src/RimTCP/1.6/Assemblies/` (DLLs).
- **Docs**: `site/` (generated by MkDocs).

## 8. Technology-Specific Organization

### .NET-Specific

- **NuGet**: Managed via `.csproj` PackageReferences.
- **Harmony**: Patches located in `src/RimTCP/RimTCP/` (e.g., `TickPatch.cs`).

### Python-Specific

- **Dependency Management**: `uv` is the standard tool. `uv.lock` ensures reproducible builds.
- **Virtual Envs**: `.venv` folders in project roots.

## 9. Extension and Evolution

### Extension Points

- **New Services**: Add to `src/RimTCP/RimTCP/Services/` and register in `TcpProtobufServer`.
- **New RL Algorithms**: Add to `src/RimGym/src/policies/`.

### Scalability

- The monorepo structure allows adding new microservices (e.g., a separate training logger) under `src/` without disrupting existing projects.

## 10. Structure Templates

### New Feature Template (RimTCP)

When adding a new game feature to the mod:

```text
src/RimTCP/RimTCP/
├── Services/
│   └── NewFeatureService.cs    # Business logic
├── DTOs/
│   └── NewFeatureData.cs       # Data structure
└── Adapters/
    └── NewFeatureAdapter.cs    # Proto conversion
```

### New RL Policy Template (RimGym)

When adding a new reinforcement learning policy:

```text
src/RimGym/src/policies/
└── new_policy/
    ├── __init__.py
    ├── config.py               # Hyperparameters
    ├── network.py              # Neural network definition
    └── trainer.py              # Training loop
```

## 11. Structure Enforcement

- **CI/CD**: GitHub Actions workflows (in `.github/workflows`) should enforce build and test passes for all sub-projects.
- **Documentation**: This blueprint serves as the reference. Changes to structure must be reflected here.

---
Last Updated: 2025-12-11
