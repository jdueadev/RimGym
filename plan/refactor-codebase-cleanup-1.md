---
goal: Refactor RimWorld ML Bridge to Production-Quality State
version: 1.0
date_created: 2025-12-11
last_updated: 2025-12-11
owner: Project Archotech Team
status: 'Planned'
tags: ['refactor', 'cleanup', 'documentation', 'technical-debt', 'production-hardening']
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

This implementation plan provides a comprehensive roadmap for refactoring the RimWorld ML Bridge codebase from its current development state to a clean, production-ready state. The project has successfully completed Phases I-V with extensive functionality, but significant technical debt and documentation inconsistencies have accumulated. This plan addresses code cleanup, documentation consolidation, architectural improvements, and production hardening.

## Analysis Summary

### Current State Assessment

**Strengths:**

- ✅ Core functionality complete (TCP+Protobuf server, Hybrid Valve, Python client)
- ✅ Rich state extraction (Phase V: Map, Incidents, World data)
- ✅ Comprehensive test coverage (116 unit tests, integration tests)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Docker integration testing

**Technical Debt Identified:**

1. **Deprecated/Legacy Code**: `GrpcService.cs` still exists but is unused (TCP replaced gRPC)
2. **Placeholder Values**: Harmony ID uses `"com.yourname.rimworldmlbridge"` instead of actual author
3. **Incomplete TODOs**: 20+ TODO comments scattered across codebase
4. **Deprecated Protobuf Messages**: `EntityState` marked deprecated but not removed
5. **Inconsistent Documentation**: Multiple overlapping docs, outdated references to gRPC
6. **Hardcoded Values**: Magic numbers in multiple files without constants
7. **Missing Metrics Integration**: SpectatorClient has TODO for metrics_collector wiring

**Documentation Issues:**

1. **Outdated References**: README and docs still reference gRPC in places
2. **Scattered Implementation Notes**: 14 files in `docs/implementation/` with overlapping content
3. **Inconsistent Version Numbers**: Different versions across files
4. **Missing API Documentation**: Partial MkDocs setup, incomplete API reference
5. **Orphaned Plan Files**: Old plans in `plan/` directory no longer current
6. **Memory Bank Staleness**: Task index shows TASK005 pending but is actually complete

**Code Organization Issues:**

1. **Test File Duplication**: Multiple test files with similar names (test_connection.py, test_tcp_connection.py)
2. **Placeholder Test**: `UnitTest1.cs` contains only a placeholder test
3. **Inconsistent Naming**: Mix of naming conventions (snake_case, PascalCase in Python)
4. **Missing Type Hints**: Some Python files lack comprehensive type annotations

## 1. Requirements & Constraints

### Requirements

- **REQ-001**: Remove all deprecated/legacy code that is no longer used
- **REQ-002**: Update all placeholder values with correct project information
- **REQ-003**: Resolve or document all TODO comments with actionable items
- **REQ-004**: Consolidate scattered documentation into unified structure
- **REQ-005**: Update all outdated references (gRPC → TCP, version numbers)
- **REQ-006**: Ensure consistent code style across C# and Python codebases
- **REQ-007**: Complete type annotations for all Python public APIs
- **REQ-008**: Remove or complete all placeholder tests
- **REQ-009**: Synchronize Memory Bank with actual project state
- **REQ-010**: Create single source of truth for architecture documentation

### Constraints

- **CON-001**: Must maintain backward compatibility with existing Python client code
- **CON-002**: Must not break existing CI/CD pipelines
- **CON-003**: Must preserve working Docker integration tests
- **CON-004**: Refactoring must be incremental with validation after each phase
- **CON-005**: Documentation updates must not require code changes
- **CON-006**: Must complete within development branch before merge to main

### Guidelines

- **GUD-001**: Follow existing C# code style (RimWorld modding conventions)
- **GUD-002**: Follow PEP 8 and Ruff linting rules for Python
- **GUD-003**: Use semantic versioning (SemVer) for all version updates
- **GUD-004**: Document all breaking changes in CHANGELOG
- **GUD-005**: Update copilot-instructions.md to reflect current architecture

### Patterns

- **PAT-001**: Single Responsibility - each file should have one clear purpose
- **PAT-002**: DRY (Don't Repeat Yourself) - consolidate duplicate documentation
- **PAT-003**: Self-documenting code - prefer clear naming over comments

## 2. Implementation Steps

### Implementation Phase 1: Code Cleanup - Legacy Removal

- GOAL-001: Remove deprecated and unused code artifacts

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Delete `RimworldMLBridge/GrpcService.cs` - unused legacy gRPC service (TCP is used instead) | ✅ | 2025-12-11 |
| TASK-002 | Remove deprecated `EntityState` message from `mlbridge.proto` (replaced by `ColonistState`) | ✅ | 2025-12-11 |
| TASK-003 | Delete `python/test_connection.py` if duplicate of `test_tcp_connection.py` | ✅ | 2025-12-11 |
| TASK-004 | Remove or convert `RimworldMLBridge.Tests/UnitTest1.cs` placeholder to real test | ✅ | 2025-12-11 |
| TASK-005 | Remove unused gRPC stubs from `python/mlbridge_pb2_grpc.py` if TCP-only | ✅ | 2025-12-11 |
| TASK-006 | Clean up `1.6/Assemblies/` - verify only necessary DLLs are present | ✅ | 2025-12-11 |

### Implementation Phase 2: Placeholder & Hardcoded Value Updates

- GOAL-002: Replace all placeholder values with correct project information

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Update Harmony ID in `RimworldMLBridge.cs` from `"com.yourname.rimworldmlbridge"` to `"com.jmduea.rimworldmlbridge"` | ✅ | 2025-12-11 |
| TASK-008 | Update `docs/guides/steam-workshop-upload.md` author placeholder from `YourName` to actual author | ✅ | 2025-12-11 |
| TASK-009 | Update `.github/copilot-instructions.md` Harmony ID reference to match actual value | ✅ | 2025-12-11 |
| TASK-010 | Create `Constants.cs` file with port number (50051), heartbeat interval (30s), max errors (10) | ✅ | 2025-12-11 |
| TASK-011 | Create Python `config.py` with default host/port/timeout constants | ✅ | 2025-12-11 |
| TASK-012 | Standardize version number across `pyproject.toml`, `About.xml`, `client/__init__.py` to 0.5.0 | ✅ | 2025-12-11 |

### Implementation Phase 3: TODO Resolution

- GOAL-003: Address all TODO comments with proper implementation or documentation

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | `TcpProtobufServer.cs:370` - Implement RESET command or document as not-implemented in protocol | | |
| TASK-014 | `TcpProtobufServer.cs:375` - Implement EXECUTE_ACTION command or create Phase VI roadmap | | |
| TASK-015 | `TcpProtobufServer.cs:649,677,696` - Implement storyteller/world data extraction TODOs | | |
| TASK-016 | `GrpcService.cs:56-57,92-93` - If not deleted, fix date calculation TODOs | | |
| TASK-017 | `ColonistAdapter.cs:44-46` - Extract IsDrafted, IsDowned, IsDead from pawn properly | | |
| TASK-018 | `gym_env/rimworld_env.py:258,270` - Document RESET/STEP limitations or implement | | |
| TASK-019 | `gym_env/rewards.py:212,230` - Add work/resource tracking placeholders to roadmap | | |
| TASK-020 | `spectator_client.py:216,231` - Wire up metrics_collector to InferenceThread and ActorThread | | |

### Implementation Phase 4: Documentation Consolidation

- GOAL-004: Consolidate scattered documentation into unified, authoritative structure

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-021 | Create `docs/architecture/README.md` consolidating: ARCHITECTURE.md, REAL_TIME_ARCHITECTURE_UPDATE.md, PHASE_IV/V_ARCHITECTURE.md | | |
| TASK-022 | Move all implementation notes from `docs/implementation/` into single `CHANGELOG.md` or archive folder | | |
| TASK-023 | Update `README.md` to remove all gRPC references, update to TCP+Protobuf terminology | | |
| TASK-024 | Update `docs/guides/installation.md` to reflect current UV-based Python setup | | |
| TASK-025 | Complete `docs/api/python/overview.md` with all public API documentation | | |
| TASK-026 | Create `docs/CHANGELOG.md` from scattered implementation summaries | | |
| TASK-027 | Archive or delete `docs/implementation/GRPC_MIGRATION.md` (historical, no longer relevant) | | |
| TASK-028 | Update `mkdocs.yml` navigation to reflect consolidated structure | | |

### Implementation Phase 5: Memory Bank Synchronization

- GOAL-005: Synchronize Memory Bank with actual project state

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-029 | Update `memory-bank/activeContext.md` to reflect current Phase (V complete, refactoring) | | |
| TASK-030 | Update `memory-bank/progress.md` - mark all Phase V tasks as complete, remove in-progress markers | | |
| TASK-031 | Update `memory-bank/tasks/_index.md` - mark TASK005 as complete (was never started, remove or close) | | |
| TASK-032 | Update `memory-bank/techContext.md` with current dependencies and build instructions | | |
| TASK-033 | Update `memory-bank/systemPatterns.md` with current architecture patterns | | |
| TASK-034 | Archive completed task files in `memory-bank/tasks/` with completion dates | | |

### Implementation Phase 6: Code Style & Type Safety

- GOAL-006: Ensure consistent code style and complete type annotations

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-035 | Run `ruff format` on all Python files and fix any issues | | |
| TASK-036 | Run `ruff check` and fix all linting errors | | |
| TASK-037 | Add comprehensive type hints to `python/client/connection.py` | | |
| TASK-038 | Add comprehensive type hints to `python/client/spectator_client.py` | | |
| TASK-039 | Add comprehensive type hints to `python/policies/` files | | |
| TASK-040 | Add comprehensive type hints to `python/gym_env/` files | | |
| TASK-041 | Run `mypy --strict` and fix type errors in core modules | | |
| TASK-042 | Add XML documentation comments to all public C# classes/methods | | |

### Implementation Phase 7: Test Cleanup & Coverage

- GOAL-007: Clean up test files and improve coverage

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-043 | Delete or rename duplicate test files in `python/` root (consolidate with `python/tests/`) | | |
| TASK-044 | Move `test_hybrid_valve.py`, `test_phase_iv1.py`, `test_tcp_connection.py` to `python/tests/` | | |
| TASK-045 | Add tests for MapAdapter, IncidentAdapter, WorldAdapter (Phase V adapters) | | |
| TASK-046 | Add integration test for full state extraction pipeline | | |
| TASK-047 | Remove or implement proper tests for `RimworldMLBridge.Tests/UnitTest1.cs` | | |
| TASK-048 | Generate and review test coverage report (target: >80%) | | |

### Implementation Phase 8: CI/CD & Build Improvements

- GOAL-008: Improve build reliability and CI/CD robustness

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-049 | Consolidate duplicate workflow files (ci.yml, build-and-test.yml, pr-validation.yml) | | |
| TASK-050 | Add version extraction from git tags to CI pipeline | | |
| TASK-051 | Create release checklist template for Steam Workshop / PyPI releases | | |
| TASK-052 | Add pre-commit hooks configuration (`.pre-commit-config.yaml`) | | |
| TASK-053 | Add automatic CHANGELOG generation from commit messages | | |
| TASK-054 | Verify all workflow files use consistent Python/dotnet versions | | |

### Implementation Phase 9: Final Validation & Documentation

- GOAL-009: Validate all changes and finalize documentation

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-055 | Run full test suite (Python + C#) and verify 100% pass rate | | |
| TASK-056 | Run Docker integration tests and verify all modes pass | | |
| TASK-057 | Build MkDocs site and verify all pages render correctly | | |
| TASK-058 | Update `copilot-instructions.md` to reflect refactored architecture | | |
| TASK-059 | Create PR description template with refactoring summary | | |
| TASK-060 | Final review of all changed files before merge | | |

## 3. Alternatives

- **ALT-001**: Keep GrpcService.cs for potential future gRPC re-enablement - Rejected: Code is 2+ months stale, creates confusion, can be recreated if needed
- **ALT-002**: Keep all implementation docs as historical record - Rejected: Move to archive folder instead, reduces noise
- **ALT-003**: Gradual TODO resolution over multiple releases - Rejected: One comprehensive cleanup is more efficient
- **ALT-004**: Automated TODO-to-Issue conversion - Considered: Could add GitHub Action, but manual review preferred for context

## 4. Dependencies

- **DEP-001**: Python 3.11+ with UV package manager
- **DEP-002**: .NET Framework 4.8 SDK
- **DEP-003**: Docker for integration testing
- **DEP-004**: Ruff for Python linting/formatting
- **DEP-005**: MyPy for Python type checking
- **DEP-006**: MkDocs with Material theme for documentation
- **DEP-007**: Git for version control and history preservation

## 5. Files

### Files to Delete

- **FILE-D001**: `RimworldMLBridge/GrpcService.cs` - Legacy gRPC service (replaced by TcpProtobufServer)
- **FILE-D002**: `RimworldMLBridge.Tests/UnitTest1.cs` - Placeholder test with no value
- **FILE-D003**: `python/test_connection.py` - If duplicate of test_tcp_connection.py

### Files to Create

- **FILE-C001**: `RimworldMLBridge/Constants.cs` - Centralized constants
- **FILE-C002**: `python/client/config.py` - Python client configuration constants
- **FILE-C003**: `docs/CHANGELOG.md` - Consolidated changelog
- **FILE-C004**: `docs/architecture/README.md` - Unified architecture documentation
- **FILE-C005**: `.pre-commit-config.yaml` - Pre-commit hooks configuration
- **FILE-C006**: `docs/archive/` - Directory for historical implementation notes

### Files to Modify

- **FILE-M001**: `RimworldMLBridge/RimworldMLBridge.cs` - Update Harmony ID
- **FILE-M002**: `Protos/mlbridge.proto` - Remove deprecated EntityState message
- **FILE-M003**: `README.md` - Remove gRPC references, update architecture section
- **FILE-M004**: `.github/copilot-instructions.md` - Update to reflect current architecture
- **FILE-M005**: `pyproject.toml` - Update version to 0.5.0
- **FILE-M006**: `About/About.xml` - Update version if needed
- **FILE-M007**: `python/client/__init__.py` - Update version to 0.5.0
- **FILE-M008**: `memory-bank/*.md` - All memory bank files need synchronization
- **FILE-M009**: `docs/guides/installation.md` - Update for UV-based setup
- **FILE-M010**: `TcpProtobufServer.cs` - Resolve TODOs or document limitations
- **FILE-M011**: `ColonistAdapter.cs` - Fix IsDrafted/IsDowned/IsDead extraction

## 6. Testing

- **TEST-001**: After Phase 1 (Legacy Removal) - Verify build succeeds, all tests pass
- **TEST-002**: After Phase 2 (Placeholder Updates) - Verify mod loads in RimWorld
- **TEST-003**: After Phase 3 (TODO Resolution) - Run full test suite
- **TEST-004**: After Phase 4 (Documentation) - Build MkDocs, verify navigation
- **TEST-005**: After Phase 6 (Code Style) - Run ruff/mypy, verify no errors
- **TEST-006**: After Phase 7 (Test Cleanup) - Generate coverage report
- **TEST-007**: After Phase 8 (CI/CD) - Run all GitHub Actions workflows
- **TEST-008**: Final validation - Docker integration tests (all 4 speeds)

## 7. Risks & Assumptions

### Risks

- **RISK-001**: Removing GrpcService.cs may break unknown dependencies - Mitigation: Search for all usages before deletion
- **RISK-002**: Proto schema changes may break Python client - Mitigation: Regenerate Python bindings, run tests
- **RISK-003**: Documentation consolidation may lose important historical context - Mitigation: Use archive folder
- **RISK-004**: Type annotation additions may reveal latent bugs - Mitigation: This is actually a benefit, fix bugs found
- **RISK-005**: CI/CD workflow consolidation may break builds - Mitigation: Test in separate branch first

### Assumptions

- **ASSUMPTION-001**: All Phase I-V functionality is complete and working
- **ASSUMPTION-002**: Docker integration tests are the source of truth for validation
- **ASSUMPTION-003**: Memory Bank reflects intended design, not just current state
- **ASSUMPTION-004**: Version 0.5.0 is appropriate for post-refactoring release
- **ASSUMPTION-005**: No new features will be added during refactoring phase

## 8. Related Specifications / Further Reading

- [TCP_PROTOBUF_IMPLEMENTATION.md](docs/implementation/TCP_PROTOBUF_IMPLEMENTATION.md) - Current implementation details
- [PHASE_V_ARCHITECTURE.md](docs/specs/PHASE_V_ARCHITECTURE.md) - Phase V rich state architecture
- [ARCHITECTURE.md](docs/specs/ARCHITECTURE.md) - Original Project Aether theoretical framework
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Memory Bank Structure](.github/instructions/memory-bank.instructions.md) - Memory Bank documentation standards
