# Multi-stage build for RimTCP testing
# Stage 1: Base image with .NET and Python
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS base

# Install all system dependencies in one layer
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

# Install UV for Python package management (official Docker method)
RUN curl -LsSf https://astral.sh/uv/install.sh | env INSTALLER_NO_MODIFY_PATH=1 sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx && \
    uv --version

# Set up working directory
WORKDIR /app

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
FROM rimworld-base AS builder

COPY . /app/

# Restore and build C# project
# The .csproj will automatically use Krafs.Rimworld.Ref NuGet package
# when local RimWorld DLLs are not available
RUN dotnet restore src/RimTCP/RimTCP/RimTCP.sln && \
    dotnet build src/RimTCP/RimTCP/RimTCP.sln -c Release

# Install Python dependencies
RUN uv sync

# Generate protobuf bindings
RUN uv run python src/shared/python/src/generate_proto.py

# Stage 4: Test runtime
FROM rimworld-base AS test-runner

# Copy built artifacts
COPY --from=builder /app/1.6 /app/1.6
COPY --from=builder /app/About /app/About
COPY --from=builder /app/Protos /app/Protos
COPY --from=builder /app/python /app/python
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
