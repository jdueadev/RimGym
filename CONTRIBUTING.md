# Contributing to RimGym

Thank you for your interest in contributing to RimGym! This guide will help you get started with development and ensure a smooth contribution process.

## Getting Started

### Prerequisites

- **Python 3.11+** - For the Python client and tests
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager
- **RimWorld 1.6+** - For running integration tests (available via Steam)
- **Git** - For version control
- **.NET 8.0 SDK** - Only if modifying the C# mod (optional)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jmduea/RimGym.git
   cd RimGym
   ```

2. **Install RimGym package**
   ```bash
   cd src/RimGym
   uv sync                    # Install dependencies from pyproject.toml
   uv pip install -e .        # Install package in editable mode
   ```

3. **Verify installation**
   ```bash
   # Test imports
   uv run python -c "from client import SpectatorClient; print('✓ Imports OK')"
   
   # Run unit tests
   uv run pytest tests/client/ -v
   
   # All tests should pass (or skip if RimWorld not running)
   ```

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**
   - Follow the code style guidelines below
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**
   ```bash
   # Unit tests (fast, no RimWorld required)
   uv run pytest tests/client/ -v
   
   # Gym environment tests
   uv run pytest tests/gym_env/ -v
   
   # Integration tests (requires RimWorld running with RimTCP mod)
   uv run pytest tests/integration/ -v
   ```

4. **Commit with meaningful message**
   ```bash
   git commit -m "feat: add new feature"
   ```
   See [Commit Message Convention](#commit-message-convention) below.

5. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   ```
   Then create a pull request on GitHub. Use our [PR template](.github/PULL_REQUEST_TEMPLATE.md) to provide all necessary information.

## Running Tests

### Unit Tests

Fast tests that don't require RimWorld:

```bash
# Test client module
uv run pytest tests/client/ -v

# Test gym environment
uv run pytest tests/gym_env/ -v

# Run with coverage
uv run pytest tests/client/ --cov=src/client --cov-report=html
```

### Integration Tests

Require a running RimWorld instance with the RimTCP mod:

```bash
# 1. Start RimWorld with RimTCP mod first
# 2. Load a save game
# 3. Run integration tests
uv run pytest tests/integration/ -v

# Run specific integration test
uv run pytest tests/integration/test_tcp_connection.py -v
```

### Performance Tests

```bash
# Run performance benchmarks
uv run pytest -m performance -v

# Run with timeout for long-running tests
uv run pytest -m performance --timeout=300 -v
```

### Running All Tests

```bash
# From src/RimGym directory
uv run pytest tests/ -v

# Skip integration tests if RimWorld not available
uv run pytest tests/ -v -m "not integration"
```

## Code Style

### Python Guidelines

- **Follow PEP 8** - Use standard Python style conventions
- **Use type hints** - Add type annotations to function signatures
- **Add docstrings** - Document public functions, classes, and modules
- **Keep functions focused** - Each function should do one thing well
- **Use descriptive names** - Variable and function names should be clear

### Code Formatting

We use `ruff` for linting and formatting:

```bash
# Format code
uv run ruff format .

# Check for linting issues
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .
```

### Type Checking

We use `mypy` for static type checking:

```bash
# Run type checker
uv run mypy src/
```

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]

[optional footer]
```

### Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or fixes
- `refactor:` - Code refactoring (no functional changes)
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks (dependencies, configs, etc.)
- `ci:` - CI/CD changes
- `style:` - Code style changes (formatting, no logic changes)

### Examples

```bash
feat: add support for multiple colonies
fix: resolve connection timeout in SpectatorClient
docs: update installation guide for Windows users
test: add unit tests for ConnectionManager
refactor: simplify state extraction logic
```

See [COMMIT_MESSAGE.md](COMMIT_MESSAGE.md) for detailed guidelines.

## Project Structure

```
RimGym/
├── src/
│   ├── RimTCP/              # C# mod for RimWorld
│   ├── RimGym/              # Python client and Gymnasium environment
│   │   ├── src/
│   │   │   ├── client/      # TCP client and spectator implementation
│   │   │   ├── gym_env/     # Gymnasium environment wrapper
│   │   │   ├── policies/    # RL policies (executive and reflex)
│   │   │   └── examples/    # Example scripts
│   │   ├── tests/           # Test suite
│   │   │   ├── client/      # Unit tests for client
│   │   │   ├── gym_env/     # Unit tests for gym environment
│   │   │   └── integration/ # Integration tests
│   │   └── pyproject.toml   # Python package configuration
│   ├── RimStats/            # Dashboard (React + FastAPI)
│   └── shared/              # Shared protobuf definitions
├── docs/                    # Documentation
├── scripts/                 # Build and deployment scripts
└── tests/                   # Root-level integration tests
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'client'"

**Solution:** Install the package in editable mode:

```bash
cd src/RimGym
uv pip install -e .
```

### Tests fail with import errors

**Check if package is installed:**

```bash
uv pip list | grep rimgym
```

If not listed, run:

```bash
cd src/RimGym
uv pip install -e .
```

### Integration tests all skip

**Cause:** RimWorld server is not running or not accessible.

**Solution:**
1. Start RimWorld
2. Enable the RimTCP mod
3. Load a save game
4. Verify the server is listening on port 50051:
   ```bash
   # On Linux/Mac
   netstat -an | grep 50051
   
   # On Windows
   netstat -an | findstr 50051
   ```

### "uv: command not found"

**Install uv:**

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### Python version issues

**Check Python version:**

```bash
python --version  # Should be 3.11 or higher
```

**Install Python 3.11+ if needed:**

- Use [pyenv](https://github.com/pyenv/pyenv) (recommended)
- Or download from [python.org](https://www.python.org/downloads/)

### Tests pass locally but fail in CI

1. Ensure all dependencies are in `pyproject.toml`
2. Check for hardcoded paths or environment-specific code
3. Review CI logs for specific error messages
4. Test in a clean virtual environment:
   ```bash
   cd src/RimGym
   rm -rf .venv uv.lock
   uv sync
   uv run pytest tests/
   ```

## Documentation

### Updating Documentation

- **Code documentation** - Add/update docstrings in code
- **User guides** - Update files in `docs/guides/`
- **API reference** - Auto-generated from docstrings
- **README** - Keep high-level overview current

### Building Documentation Locally

```bash
cd src/RimGym
uv sync --group docs
uv run mkdocs serve
# Visit http://localhost:8000
```

## Getting Help

- **Check existing documentation:**
  - [README.md](README.md) - Project overview
  - [docs/](docs/) - Detailed documentation
  - [src/RimGym/README.md](src/RimGym/README.md) - Python client docs
  - [src/RimTCP/README.md](src/RimTCP/README.md) - C# mod docs

- **Search for similar issues:**
  - [GitHub Issues](https://github.com/jmduea/RimGym/issues)
  - [Closed Issues](https://github.com/jmduea/RimGym/issues?q=is%3Aissue+is%3Aclosed)

- **Ask for help:**
  - [Open an issue](https://github.com/jmduea/RimGym/issues/new) for bugs
  - [Start a discussion](https://github.com/jmduea/RimGym/discussions) for questions
  - Check our [Code of Conduct](CODE_OF_CONDUCT.md) before posting

## Review Process

### What to Expect

1. **Automated checks** - CI runs tests and linters
2. **Code review** - Maintainers review your changes
3. **Discussion** - Questions or suggestions may be provided
4. **Approval** - Once approved, your PR will be merged

### Review Criteria

- Code follows style guidelines
- Tests pass and coverage is maintained
- Documentation is updated
- Commit messages follow conventions
- Changes are focused and well-explained

See [CODE_REVIEW.md](CODE_REVIEW.md) for detailed review standards.

## Additional Resources

- [Architecture Documentation](docs/architecture/README.md)
- [Phase IV Architecture](docs/specs/PHASE_IV_ARCHITECTURE.md) - Python client design
- [Phase V Architecture](docs/specs/PHASE_V_ARCHITECTURE.md) - Observability design
- [TCP Protocol](docs/implementation/TCP_PROTOBUF_IMPLEMENTATION.md)
- [Docker Quick Start](docs/docker/QUICKSTART.md)
- [Testing Automation](src/RimGym/TESTING_AUTOMATION.md)

## License

By contributing to RimGym, you agree that your contributions will be licensed under the same license as the project. See [LICENSE](LICENSE) for details.

---

**Thank you for contributing to RimGym!** 🎉
