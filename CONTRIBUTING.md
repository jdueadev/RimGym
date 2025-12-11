# Contributing to RimWorld ML Bridge

Thank you for your interest in contributing! This project bridges RimWorld with machine learning frameworks, enabling AI agents to interact with the game. Whether you're a modder, ML researcher, or developer, we welcome your contributions.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Contributing Guidelines](#contributing-guidelines)
- [Testing Requirements](#testing-requirements)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## 📜 Code of Conduct

This project follows a standard code of conduct. Be respectful, inclusive, and constructive in all interactions.

## 🚀 Getting Started

### Prerequisites

**For C# Development (RimWorld Mod)**:

- Visual Studio 2022 or VS Code with C# extension
- .NET Framework 4.8 SDK
- RimWorld 1.6+ installed
- Harmony mod (automatically loaded from Steam Workshop)

**For Python Development (ML Client)**:

- Python 3.11+
- [UV package manager](https://github.com/astral-sh/uv) (strongly recommended)
- Basic understanding of asyncio and threading

**For Docker Development**:

- Docker Desktop or Docker Engine
- docker-compose

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/jmduea/RimworldMLBridge.git
cd RimworldMLBridge

# Set up Python environment
uv sync --all-extras

# Build C# mod
dotnet build RimworldMLBridge.sln -c Release

# Run tests
uv run pytest python/tests/
dotnet test RimworldMLBridge.Tests/
```

## 📁 Project Structure

```
RimworldMLBridge/
├── RimworldMLBridge/          # C# mod source code
│   ├── RimworldMLBridge.cs    # Mod entry point
│   ├── TcpProtobufServer.cs   # Network server
│   ├── Services/              # RIMAPI-style data extraction
│   └── Adapters/              # DTO → Protobuf converters
├── python/
│   ├── client/                # Python client (Listener/Inference/Actor threads)
│   ├── policies/              # Executive and Reflex policies
│   ├── gym_env/               # Gymnasium environment wrapper
│   ├── examples/              # Example scripts
│   └── tests/                 # Python unit and integration tests
├── Protos/
│   └── mlbridge.proto         # Protocol Buffers schema (single source of truth)
├── docker/                    # Docker configuration and scripts
├── docs/                      # Documentation
└── .github/                   # CI/CD workflows and issue templates
```

## 🤝 Contributing Guidelines

### Types of Contributions

We welcome:

1. **Bug Fixes**: Found a bug? Fix it and submit a PR!
2. **Feature Additions**: New capabilities for the mod or client
3. **Documentation**: Improvements to guides, API docs, or examples
4. **Performance Optimizations**: Make it faster!
5. **Test Coverage**: Add tests for untested code
6. **Examples**: Demo scripts showcasing features

### Before You Start

1. **Check existing issues**: Someone might already be working on it
2. **Open an issue first**: For major features, discuss the design before implementing
3. **Read the architecture docs**: Understand the system design ([ARCHITECTURE.md](docs/specs/ARCHITECTURE.md))

## 🛠️ Development Setup

### C# Mod Development

1. **Set RimWorld path** in `RimworldMLBridge.csproj`:

   ```xml
   <RimWorldPath>C:\Program Files (x86)\Steam\steamapps\common\RimWorld</RimWorldPath>
   ```

2. **Build the mod**:

   ```bash
   dotnet build RimworldMLBridge.sln -c Release
   ```

3. **Output location**: Built assemblies go to `1.6/Assemblies/`

4. **Testing in RimWorld**:
   - Copy entire mod folder to `RimWorld/Mods/`
   - Enable in game mod settings
   - Check `Player.log` for errors

### Python Client Development

1. **Install dependencies**:

   ```bash
   uv sync --all-extras  # Includes dev and training extras
   ```

2. **Run tests**:

   ```bash
   uv run pytest python/tests/ -v
   ```

3. **Type checking**:

   ```bash
   uv run mypy python/client python/policies
   ```

4. **Linting**:

   ```bash
   uv run ruff check python/
   uv run ruff format python/
   ```

### Docker Development

1. **Build and test locally**:

   ```bash
   docker-compose up test
   ```

2. **Run integration tests**:

   ```bash
   uv run pytest python/tests/integration/ -v
   ```

## ✅ Testing Requirements

### Unit Tests (Required)

- **Python**: All new code must have unit tests
  - Use `pytest` for testing
  - Target 80%+ code coverage
  - Test edge cases and error handling

- **C#**: Add tests to `RimworldMLBridge.Tests/`
  - Use MSTest or xUnit
  - Mock RimWorld dependencies where possible

### Integration Tests (Recommended)

- Test actual communication between C# mod and Python client
- Use Docker for reproducible testing
- Tests should pass in CI environment

### Running Tests

```bash
# Python unit tests
uv run pytest python/tests/ -v --cov=client --cov=policies

# Python integration tests (requires Docker)
docker-compose up -d test
uv run pytest python/tests/integration/ -v

# C# tests
dotnet test RimworldMLBridge.Tests/
```

## 📝 Coding Standards

### C# Style

Follow standard C# conventions:

- **Naming**:
  - PascalCase for classes, methods, properties
  - camelCase for local variables, parameters
  - _camelCase for private fields
- **Threading**: NEVER access Unity/RimWorld objects from background threads
- **Logging**: Use `[MLBridge]` prefix for all log messages
- **Null checks**: Use null-conditional operators (`?.`, `??`)
- **Error handling**: Wrap Unity API calls in try-catch with graceful degradation

**Example**:

```csharp
public class MyService
{
    private readonly ILogger _logger;
    
    public List<ColonistDTO> GetColonists()
    {
        try
        {
            if (Current.Game?.CurrentMap == null)
            {
                _logger.Warning("[MLBridge] No active map");
                return new List<ColonistDTO>();
            }
            
            // Extract colonist data
            return Current.Game.CurrentMap.mapPawns.FreeColonistsSpawned
                .Select(p => ConvertToDTO(p))
                .ToList();
        }
        catch (Exception ex)
        {
            _logger.Error($"[MLBridge] Error getting colonists: {ex}");
            return new List<ColonistDTO>();
        }
    }
}
```

### Python Style

Follow PEP 8 with these specifics:

- **Type hints**: Use type hints for all public methods
- **Docstrings**: Use Google-style docstrings
- **Formatting**: Use `ruff format` (black-compatible)
- **Imports**: Use `isort` (integrated in ruff)
- **Line length**: 100 characters (not 88)

**Example**:

```python
from typing import Optional
import asyncio

class ConnectionManager:
    """Manages TCP connection to RimWorld server with auto-reconnect.
    
    Attributes:
        host: Server hostname or IP address.
        port: Server port number.
        auto_reconnect: Whether to automatically reconnect on failure.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        *,
        auto_reconnect: bool = True,
    ) -> None:
        """Initialize connection manager.
        
        Args:
            host: Server hostname.
            port: Server port.
            auto_reconnect: Enable automatic reconnection.
        """
        self.host = host
        self.port = port
        self._auto_reconnect = auto_reconnect
        self._socket: Optional[socket.socket] = None
    
    async def connect(self) -> bool:
        """Establish connection to server.
        
        Returns:
            True if connection successful, False otherwise.
        
        Raises:
            ConnectionError: If connection fails and auto_reconnect is False.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            await asyncio.get_event_loop().sock_connect(
                self._socket, (self.host, self.port)
            )
            return True
        except OSError as e:
            if not self._auto_reconnect:
                raise ConnectionError(f"Failed to connect: {e}") from e
            return False
```

### Protobuf Schema

- **Comments**: Document all message types and fields
- **Versioning**: Never remove fields, only deprecate
- **Naming**: Use snake_case for field names
- **Required vs Optional**: Use `optional` for nullable fields

## 🔄 Pull Request Process

### Before Submitting

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, atomic commits

3. **Run all tests**:

   ```bash
   uv run pytest python/tests/ -v
   dotnet test RimworldMLBridge.Tests/
   ```

4. **Update documentation** if needed

5. **Add changelog entry** (if applicable)

### Submitting

1. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub

3. **Fill out the PR template** completely

4. **Link related issues** (e.g., "Fixes #123")

### PR Requirements

✅ **Must Have**:

- Clear description of changes
- All tests passing
- No merge conflicts
- Code follows style guidelines

✅ **Should Have**:

- Unit tests for new code
- Updated documentation
- Changelog entry

✅ **Nice to Have**:

- Integration tests
- Performance benchmarks
- Example usage

### Review Process

1. **Automated checks** run via GitHub Actions
2. **Maintainer review** within 3-5 business days
3. **Address feedback** promptly
4. **Approval and merge** by maintainer

## 🐛 Issue Reporting

### Bug Reports

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml) and include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, versions, etc.)
- Relevant logs (RimWorld Player.log, Python traceback)

### Feature Requests

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.yml) and include:

- Problem statement
- Proposed solution
- Use case / motivation
- Implementation ideas (optional)

### Questions

Use the [Question template](.github/ISSUE_TEMPLATE/question.yml) or start a [Discussion](https://github.com/jmduea/RimworldMLBridge/discussions).

## 🎯 Good First Issues

Look for issues labeled:

- `good first issue`: Easy entry points
- `help wanted`: Community contributions welcome
- `documentation`: Non-code contributions

## 📚 Additional Resources

- [Architecture Overview](docs/specs/ARCHITECTURE.md)
- [Phase IV Architecture](docs/specs/PHASE_IV_ARCHITECTURE.md)
- [Quick Start Guide](QUICKSTART_PHASE4.md)
- [Docker Troubleshooting](docker/TROUBLESHOOTING.md)

## 🙏 Recognition

Contributors are recognized in:

- GitHub contributors list
- Release notes
- Project documentation

Thank you for contributing to RimWorld ML Bridge! 🚀
