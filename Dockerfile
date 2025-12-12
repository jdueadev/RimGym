## Multi-stage build
## Goals:
## - Keep a lean RimWorld worker runtime image (no RimGym source tree, no UV/venv).
## - Keep a separate trainer/runtime image containing RimGym + Python deps.
## - Preserve the existing `test-runner` target for dev/integration workflows.

# Stage 1: Base OS deps (runtime-friendly). No UV/venv here.
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS base

# Install all system dependencies in one layer.
RUN apt-get update && apt-get install -y \
    python3.11 \
    wget \
    curl \
    unzip \
    xvfb \
    x11vnc \
    fluxbox \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 1b: UV-enabled base (build + trainer). Keeps UV out of the RimWorld worker runtime.
FROM base AS uv-base

RUN curl -LsSf https://astral.sh/uv/install.sh | env INSTALLER_NO_MODIFY_PATH=1 sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx && \
    uv --version

# Stage 2: RimWorld base configuration
FROM base AS rimworld-base

# RimWorld installation directory
ENV RIMWORLD_PATH=/opt/rimworld
ENV DISPLAY=:99

# Create RimWorld directory
RUN mkdir -p ${RIMWORLD_PATH}

# Note: RimWorld Linux version must be provided externally due to licensing
# Options:
# 1. Build with --build-arg and mount Steam library
# 2. Copy from local installation
# 3. Use volume mount at runtime

# Stage 3: Build environment
FROM uv-base AS builder

# keep uv environment in a fixed location
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY . /app/

# Restore and build C# project
# The .csproj will automatically use Krafs.Rimworld.Ref NuGet package
# when local RimWorld DLLs are not available
RUN dotnet restore src/RimTCP/RimTCP/RimTCP.sln && \
    dotnet build src/RimTCP/RimTCP/RimTCP.sln -c Release

# Install dependencies for RimGym (pyproject.toml located in src/RimGym/)
RUN uv sync --project src/RimGym --group dev

# Generate protobuf bindings
# standalone script located at src/shared/python/src/generate_proto.py
# deps are defined in-line
RUN uv run src/shared/python/src/generate_proto.py

# Stage 4a: Lean RimWorld worker runtime (no RimGym, no UV/venv)
FROM rimworld-base AS rimworld-worker

# Ensure protobuf runtime is new enough for generated *_pb2.py.
# Debian's packaged python3-protobuf may lag behind protoc output.
RUN apt-get update && apt-get install -y \
    python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m venv /opt/rimgym/.hcvenv && \
    /opt/rimgym/.hcvenv/bin/pip install --no-cache-dir "protobuf>=6,<7"

# Copy built RimTCP artifacts
COPY --from=builder /app/src/RimTCP/1.6 /app/1.6
COPY --from=builder /app/src/RimTCP/About /app/About

# Copy only what's needed for protocol-level healthcheck
# - generated proto module
# - probe script
RUN mkdir -p /opt/rimgym/healthcheck /opt/rimgym/protos
COPY --from=builder /app/src/shared/python/src/rimgym_pb2.py /opt/rimgym/protos/rimgym_pb2.py
COPY --from=builder /app/src/RimGym/src/diagnostics/rimtcp_healthcheck_probe.py /opt/rimgym/healthcheck/rimtcp_healthcheck_probe.py

# Copy to RimWorld Mods directory
RUN mkdir -p ${RIMWORLD_PATH}/Mods/RimTCP && \
    cp -r /app/1.6 ${RIMWORLD_PATH}/Mods/RimTCP/ && \
    cp -r /app/About ${RIMWORLD_PATH}/Mods/RimTCP/

ENV DISPLAY=:99

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["server"]

# Stage 4b: Trainer runtime (RimGym + protos + venv)
FROM uv-base AS trainer

# keep uv environment in a fixed location
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=builder /app/src/shared /app/src/shared
COPY --from=builder /app/src/RimGym /app/src/RimGym
COPY --from=builder /app/.venv /app/.venv

WORKDIR /app

# Stage 4c: Test runtime (dev/integration)
FROM rimworld-base AS test-runner

# keep uv environment in a fixed location
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Copy built artifacts
COPY --from=builder /app/src/RimTCP/1.6 /app/1.6
COPY --from=builder /app/src/RimTCP/About /app/About
COPY --from=builder /app/src/shared /app/src/shared
COPY --from=builder /app/src/RimGym /app/src/RimGym
COPY --from=builder /app/.venv /app/.venv

# Copy to RimWorld Mods directory
RUN mkdir -p ${RIMWORLD_PATH}/Mods/RimTCP && \
    cp -r /app/1.6 ${RIMWORLD_PATH}/Mods/RimTCP/ && \
    cp -r /app/About ${RIMWORLD_PATH}/Mods/RimTCP/

# Set up virtual X server for headless testing
ENV DISPLAY=:99

# Entrypoint script
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["test"]
