# Documentation Consolidation & Update Plan

## Objective
Update all documentation to reflect the current project state and structure. Consolidate redundant information and ensure a clear hierarchy.

## 1. Terminology Standardization
- **RimGym**: The overarching project name.
- **RimTCP**: The C# RimWorld mod (formerly the legacy mod name).
- **RimGym (Python)**: The Python Gymnasium environment and client.
- **RimStats**: The training visualization dashboard.

## 2. Root Documentation (`/`)
- **`README.md`**:
    - [ ] Rename title to "RimGym".
    - [ ] Update description to define RimGym as the ecosystem.
    - [ ] Add a "Project Structure" section linking to:
        - `src/RimTCP` (The Mod)
        - `src/RimGym` (The Python Env)
        - `src/RimStats` (The Dashboard)
    - [ ] Update badges and links.
- **`Project_Folders_Structure_Blueprint.md`**:
    - [ ] Verify against current file structure and update.
- **`CONTRIBUTING.md`**:
    - [ ] Update for monorepo workflow (how to build mod vs python vs dashboard).

## 3. Component Documentation (`src/*`)
- **`src/RimTCP/README.md`**:
    - [ ] Create/Update to focus specifically on the Mod (installation, harmony patches, protocol).
    - [ ] Move mod-specific details from root `README.md` here.
- **`src/RimGym/README.md`**:
    - [ ] Create/Update to focus on the Python package (installation, usage, gym API).
- **`src/RimStats/README.md`**:
    - [ ] Ensure it focuses on the dashboard (already seems mostly correct).

## 4. Global Documentation (`docs/`)
- **`docs/specs/`**:
    - [ ] Review architecture specs. Update legacy naming to "RimGym" or "RimTCP" where appropriate.
- **`docs/guides/`**:
    - [ ] `installation.md`: Split into "Mod Installation" (RimTCP) and "Environment Setup" (RimGym).
    - [ ] `python-client.md`: Move content to `src/RimGym/README.md` or link to it.
- **`docs/implementation/`**:
    - [ ] Keep as historical/deep-dive, but update context notes.

## 5. Action Items
1.  **Search & Replace**: Run a global search for legacy naming and replace with "RimGym" (project context) or "RimTCP" (mod context).
2.  **Move Content**: Extract sections from root `README.md` into `src/RimTCP/README.md` and `src/RimGym/README.md`.
3.  **Update Links**: Fix relative links in all markdown files to point to the new locations.
4.  **Verify**: Check `mkdocs.yml` (if active) to ensure the site builds correctly with the new structure.

## 6. Files to Edit
- `README.md`
- `docs/README.md`
- `docs/index.md`
- `src/RimStats/README.md`
- `src/RimGym/pyproject.toml` (Update description/name if possible)
- `src/RimTCP/About/About.xml` (Verify description)
- `docs/specs/*.md`

## 7. Verification
- Verify all links are working.
- Verify terminology is consistent.
