# Code Style and Conventions

## EditorConfig

The project uses `.editorconfig` for consistent formatting. Key settings:

| File Type | Indent Style | Indent Size |
|-----------|--------------|-------------|
| Default | Spaces | 2 |
| C# (*.cs) | Spaces | 4 |
| Python (*.py) | Spaces | 4 |
| Proto (*.proto) | Spaces | 2 |
| PowerShell (*.ps1) | Spaces | 4 |
| YAML (*.yml) | Spaces | 2 |
| Markdown (*.md) | Spaces | 2, no trailing whitespace trim |

## C# Conventions

### Naming

- **Classes/Methods**: PascalCase (e.g., `ColonistAdapter`, `ToProtobuf`)
- **Private fields**: camelCase with underscore prefix (e.g., `_adapter`)
- **Constants**: PascalCase (e.g., `DefaultPort`)
- **Parameters/locals**: camelCase (e.g., `colonistDto`)

### Style

- Allman brace style (brace on new line)
- Use `var` when type is apparent from context
- Null-conditional operator (`?.`) for safe navigation
- Log prefix: `[RimTCP]` for all mod logs

### Threading Rules (CRITICAL)

- **Never** access Unity APIs (`Current.Game`, `Find.*`, `Pawn`, `Thing`) from background threads
- Queue commands via `ConcurrentQueue`, process on main thread in `Root_Update_Patch`

### Harmony Patching

- Always catch exceptions in patch bodies
- Use `[StaticConstructorOnStartup]` for initialization
- Harmony ID: `unknwnentity.rimtcp`

## Python Conventions

### Naming

- **Modules/functions**: snake_case (e.g., `spectator_client`, `get_state`)
- **Classes**: PascalCase (e.g., `SpectatorClient`, `RichGameState`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PORT`)
- **Private**: leading underscore (e.g., `_internal_method`)

### Type Hints

- Required for all public functions and methods
- Use `Optional[T]` for nullable types
- Use `list[T]` (Python 3.9+) over `List[T]`

### Docstrings

- Use Google-style docstrings for public APIs
- Include Args, Returns, Raises sections as needed

### Formatting

- Line length: 88 characters (Ruff/Black default)
- Formatter: Ruff (`uv run ruff format`)
- Linter: Ruff (`uv run ruff check`)
- Type checker: MyPy (`uv run mypy`)

## Protocol Buffers

### Field Numbering

- Never reuse field numbers
- Reserve deleted fields to prevent accidents
- Use 1-15 for frequently accessed fields (1-byte encoding)

### Message Design

- Use meaningful enum names
- Prefer flat structures over deep nesting
- Document field semantics with comments

## Git Conventions

### Branch Naming

- Feature: `feature/description`
- Fix: `fix/description`
- Current: `suite_centric_layout`

### Commit Messages

- Follow conventional commits style
- Examples: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

## File Organization

```
src/
├── RimTCP/          # C# mod
│   ├── Adapters/    # DTO → Protobuf converters
│   ├── DTOs/        # Data transfer objects
│   ├── Services/    # Game data extraction services
│   └── Diagnostics/ # Performance profiling
├── RimGym/          # Python client
│   ├── src/
│   │   ├── client/      # TCP client, threading
│   │   ├── gym_env/     # Gymnasium environment
│   │   └── policies/    # RL policies (executive/reflex)
│   └── tests/
├── RimStats/        # Dashboard
│   ├── backend/     # FastAPI
│   └── frontend/    # React + TypeScript
└── shared/
    └── Protos/      # rimgym.proto schema
```
