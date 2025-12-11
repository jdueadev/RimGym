# Quick Start Guide - Phase IV Python Client

## Prerequisites

1. RimWorld running with ML Bridge mod (or Docker container)
2. Python 3.11+
3. UV package manager

## Installation

```bash
# Navigate to project root
cd RimworldMLBridge

# Install dependencies (includes core packages)
uv sync

# Install optional training dependencies
uv sync --extra train
```

This installs:

- Core: `protobuf`, `gymnasium`, `numpy`
- Training (optional): `stable-baselines3`, `tensorboard`
- Dev: `pytest`, `pytest-cov`

## Running Examples

All example scripts are in `python/examples/` directory.

### 1. Spectator Demo (Observation Only)

Watch RimWorld game state without taking actions:

```bash
# Start RimWorld (if using Docker)
docker-compose up test

# In another terminal, run spectator demo
uv run python python/examples/spectator_demo.py --duration 60
```

### 2. Train an RL Agent

Train a PPO agent using Stable-Baselines3:

```bash
# Ensure training dependencies installed
uv sync --extra train

# Train agent
uv run python python/examples/train_agent.py \
    --timesteps 100000 \
    --save-freq 10000 \
    --log-dir ./logs
```

Training features:

- Automatic checkpointing every 10k steps
- Evaluation every 5k steps
- TensorBoard logging
- Interrupt handling (Ctrl+C saves model)

### 3. Run Trained Agent (Inference)

Deploy a trained model in inference mode:

```bash
uv run python python/examples/run_inference.py \
    ./logs/best_model/best_model.zip \
    --duration 300
```

## Running Tests

### Unit Tests

```bash
# Run all unit tests
uv run pytest python/tests/

# Run specific test module
uv run pytest python/tests/client/test_listener.py -v

# Run with coverage
uv run pytest --cov=client --cov=policies --cov=gym_env python/tests/
```

### Integration Tests (Requires Docker)

```bash
# Start RimWorld test server
docker-compose up test

# In another terminal, run integration tests
uv run pytest python/tests/integration/ -v

# Run specific integration test
uv run pytest python/tests/integration/test_full_system.py::TestFullClientIntegration -v
```

### Performance Benchmarks

```bash
# Requires running RimWorld server
uv run pytest python/tests/integration/test_performance.py -v
```

## Project Structure

```
RimworldMLBridge/
├── python/
│   ├── client/          # Core client components
│   │   ├── connection.py
│   │   ├── spectator_client.py
│   │   ├── listener.py
│   │   ├── inference.py
│   │   ├── actor.py
│   │   ├── queues.py
│   │   └── metrics.py
│   ├── policies/        # Strategic and tactical policies
│   │   ├── policy.py
│   │   ├── executive.py
│   │   └── reflex.py
│   ├── gym_env/         # Gymnasium RL environment
│   │   ├── rimworld_env.py
│   │   ├── spaces.py
│   │   └── rewards.py
│   ├── examples/        # Example scripts
│   │   ├── spectator_demo.py
│   │   ├── train_agent.py
│   │   └── run_inference.py
│   └── tests/           # Test suites
│       ├── client/
│       ├── gym_env/
│       └── integration/
├── docs/
│   └── guides/
│       └── phase4_usage.md  # Comprehensive documentation
└── pyproject.toml
```

## Common Issues

### Import Errors

If you see `ModuleNotFoundError: No module named 'client'`:

```bash
# Ensure packages are installed
uv sync

# Verify installation
uv run python -c "import client; import policies; import gym_env; print('OK')"
```

### Connection Errors

If examples can't connect to RimWorld:

1. Check RimWorld is running: `docker-compose ps`
2. Check port 50051 is open: `netstat -an | Select-String "50051"`
3. Check RimWorld logs: `docker-compose logs test`

### Performance Issues

If training is slow:

- Adjust `--episode-length` (default 1000 steps)
- Use `--num-envs 1` (multiple environments requires multiple RimWorld instances)
- Check RimWorld game speed (pause if using training mode)

## Next Steps

1. Read comprehensive documentation: `docs/guides/phase4_usage.md`
2. Explore examples: `python/examples/`
3. Run tests to verify setup: `uv run pytest python/tests/client/ -v`
4. Try training a simple agent with small timesteps first

## Support

- Documentation: `docs/guides/phase4_usage.md`
- Architecture: `docs/specs/PHASE_IV_ARCHITECTURE.md`
- Implementation details: `docs/implementation/`
- Test examples: `python/tests/`
