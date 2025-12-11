# Installation Guide

This guide covers the installation of the **RimGym** ecosystem, including the **RimTCP** mod for RimWorld and the **RimGym** Python environment.

## Prerequisites

### For RimTCP (The Mod)

- **RimWorld** (Version 1.6+)
- **Harmony** (Mod dependency, usually installed via Steam Workshop)
- **.NET Framework 4.8 SDK** (For building from source)

### For RimGym (The Python Client)

- **Python 3.11+** (Recommended)
- **[uv](https://github.com/astral-sh/uv)** (Strongly recommended package manager)

---

## Part 1: Installing the RimTCP Mod

You can either install the mod from a pre-built release or build it from source.

### Option A: Build from Source (Recommended for Developers)

1. **Clone the Repository**

    ```bash
    git clone https://github.com/jmduea/RimworldMLBridge.git
    cd RimworldMLBridge
    ```

2. **Set Environment Variables**
    Set `RIMWORLD_DIR` to your RimWorld installation directory.

    **Windows (PowerShell):**

    ```powershell
    $env:RIMWORLD_DIR="C:\Program Files (x86)\Steam\steamapps\common\RimWorld"
    ```

    **Linux/Mac:**

    ```bash
    export RIMWORLD_DIR="/path/to/RimWorld"
    ```

3. **Build the Mod**

    ```bash
    dotnet build src/RimTCP/RimTCP.sln -c Release
    ```

    This will compile the mod and place the assemblies in `src/RimTCP/1.6/Assemblies/`.

4. **Install to RimWorld**
    Create a symbolic link from your RimWorld `Mods` folder to the `src/RimTCP` directory.

    **Windows (PowerShell as Admin):**

    ```powershell
    New-Item -ItemType SymbolicLink -Path "$env:RIMWORLD_DIR\Mods\RimTCP" -Target "$PWD\src\RimTCP"
    ```

    **Linux/Mac:**

    ```bash
    ln -s "$(pwd)/src/RimTCP" "$RIMWORLD_DIR/Mods/RimTCP"
    ```

5. **Enable the Mod**
    Launch RimWorld, go to **Mods**, and enable **RimTCP**. Ensure **Harmony** is loaded before it.

---

## Part 2: Setting up the RimGym Python Environment

1. **Navigate to the Python Directory**

    ```bash
    cd src/RimGym
    ```

2. **Install Dependencies**
    Using `uv` (recommended):

    ```bash
    uv sync
    ```

    Or using standard pip:

    ```bash
    pip install -e .
    ```

3. **Verify Installation**
    Run the connection test (ensure RimWorld is running with the mod enabled and a save loaded):

    ```bash
    uv run examples/test_connection.py
    ```

---

## Part 3: Setting up the Dashboard (RimStats)

See [src/RimStats/README.md](../../src/RimStats/README.md) for dashboard installation instructions.
