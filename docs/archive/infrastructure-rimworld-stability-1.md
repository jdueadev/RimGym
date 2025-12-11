---
goal: Stabilize Long-Running RimWorld Docker Instances for Integration Testing
version: 1.0
date_created: 2025-12-10
last_updated: 2025-12-10
owner: RimWorld ML Bridge Team
status: 'In progress'
tags: [infrastructure, docker, testing, stability, integration]
---

# Introduction

![Status: In progress](https://img.shields.io/badge/status-In_progress-yellow)

This plan addresses the stability issues with long-running RimWorld instances in Docker containers used for integration testing. Currently, 4 of 5 integration tests pass, but the `test_listener_thread_polling` test fails due to connection drops ("connection aborted by host"). The goal is to diagnose and resolve these stability issues, implement robust connection recovery, and enable all 16 integration tests to run reliably.

## 1. Requirements & Constraints

- **REQ-001**: RimWorld server must run continuously in Docker for at least 5 minutes without crashes
- **REQ-002**: TCP server on port 50051 must accept and handle multiple client connections
- **REQ-003**: All 16 integration tests must pass (12 full system + 4 performance benchmarks)
- **REQ-004**: Connection drops must be handled gracefully with automatic reconnection
- **REQ-005**: RimWorld logs must be accessible for debugging stability issues
- **SEC-001**: Docker container must not expose unnecessary ports or services
- **CON-001**: RimWorld runs in headless mode (-batchmode -nographics) without GPU
- **CON-002**: Must use existing rimworld-data volume with RimWorld Linux installation
- **CON-003**: Cannot modify core RimWorld behavior, only our mod (RimworldMLBridge)
- **CON-004**: Unity graphics errors in headless mode are expected and acceptable
- **GUD-001**: Use Docker health checks to monitor RimWorld server availability
- **GUD-002**: Implement exponential backoff for connection retries
- **GUD-003**: Log all connection state changes for diagnostics
- **PAT-001**: Follow the existing SpectatorClient architecture for connection management

## 2. Implementation Steps

### Phase 1: Diagnostics and Monitoring

- GOAL-001: Establish comprehensive monitoring and logging to diagnose stability issues

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Add Docker health check to integration service in docker-compose.yml that pings port 50051 every 30s | ✅ | 2025-01-XX |
| TASK-002 | Create diagnostics script (python/diagnostics/check_rimworld_health.py) to test connection, send QUERY_STATE, and log response times | ✅ | 2025-01-XX |
| TASK-003 | Add structured logging to TcpProtobufServer.cs with timestamps, connection counts, message counts, and error details | ✅ | 2025-01-XX |
| TASK-004 | Configure RimWorld log level in docker command to capture all mod initialization and TCP server events | ✅ | 2025-01-XX |
| TASK-005 | Create log aggregation script (docker/collect_logs.sh) to gather RimWorld logs, mod logs, and Docker logs into single timestamped file | ✅ | 2025-01-XX |
| TASK-006 | Run diagnostics script for 5 minutes while monitoring logs to identify failure patterns | | |

### Phase 2: RimWorld Server Stability

- GOAL-002: Improve RimWorld server stability and prevent connection drops

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Review RimworldMLBridge.cs mod initialization to ensure TCP server starts after all RimWorld systems are ready | ✅ | 2025-01-XX |
| TASK-008 | Add heartbeat mechanism in TcpProtobufServer.cs that logs "Server alive" every 30 seconds with active connection count | ✅ | 2025-01-XX |
| TASK-009 | Implement graceful error handling in ProcessCommands() to catch and log exceptions without crashing server | ✅ | 2025-01-XX |
| TASK-010 | Add connection timeout detection in TcpProtobufServer.cs to close stale connections after 60s of inactivity | | |
| TASK-011 | Test RimWorld with minimal ModsConfig.xml (only Harmony + RimworldMLBridge) to rule out mod conflicts | | |
| TASK-012 | Increase Docker container memory limit to 4GB in docker-compose.yml to prevent OOM kills | ✅ | 2025-01-XX |
| TASK-013 | Add error boundary in Root_Update_Patch to prevent mod exceptions from crashing RimWorld main loop | ✅ | 2025-01-XX |

### Phase 3: Client Connection Resilience

- GOAL-003: Implement robust connection recovery in Python client

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-014 | Add auto-reconnect configuration to ConnectionManager with max_reconnect_attempts and reconnect_backoff_ms parameters | ✅ | 2025-01-XX |
| TASK-015 | Implement automatic reconnection in ConnectionManager.send_command() when socket errors occur | ✅ | 2025-01-XX |
| TASK-016 | Add connection state monitoring in ListenerThread to detect disconnections and trigger reconnection | ✅ | 2025-01-XX |
| TASK-017 | Implement graceful degradation in SpectatorClient: continue running even if temporarily disconnected | | |
| TASK-018 | Add connection_lost and connection_restored events to EventQueue for policy awareness | ✅ | 2025-01-XX |
| TASK-019 | Update test_listener_thread_polling to allow temporary connection drops if recovery succeeds within 10s | | |
| TASK-020 | Add integration test test_connection_recovery that intentionally kills/restarts server to verify resilience | | |

### Phase 4: Integration Test Fixes

- GOAL-004: Fix remaining integration test failures and enable all 16 tests

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-021 | Fix test_listener_thread_polling by adding retry logic and increasing wait time to 2 seconds | ✅ | 2025-01-XX |
| TASK-022 | Run test_triple_threaded_coordination with extended timeout (120s) to verify full client lifecycle | | |
| TASK-023 | Enable test_env_reset, test_env_step, test_env_episode_complete by ensuring Gymnasium environment handles connection drops | | |
| TASK-024 | Run test_reconnection (currently skipped) by implementing temporary server restart mechanism | | |
| TASK-025 | Configure test_long_running_stability to run for 5 minutes with continuous state polling | | |
| TASK-026 | Fix performance benchmarks by ensuring RimWorld server is warm (run for 30s before benchmark) | | |
| TASK-027 | Create test report generator (python/tests/generate_report.py) to output JSON with pass/fail/timing for all tests | | |

### Phase 5: Docker and CI/CD Improvements

- GOAL-005: Improve Docker setup and enable automated testing in CI/CD

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-028 | Create docker/wait-for-server.sh script that blocks until port 50051 responds to QUERY_STATE command | ✅ | 2025-01-XX |
| TASK-029 | Update integration service command to use wait-for-server.sh before declaring "ready for connections" | | |
| TASK-030 | Add restart policy (restart: on-failure, max attempts: 3) to integration service in docker-compose.yml | ✅ | 2025-01-XX |
| TASK-031 | Create GitHub Actions workflow (.github/workflows/integration-tests.yml) that builds Docker image and runs tests | | |
| TASK-032 | Add caching for rimworld-data volume in CI to avoid re-setup on every run | | |
| TASK-033 | Create docker/cleanup.sh script to safely stop containers and prune old images | | |
| TASK-034 | Document complete Docker setup process in docs/guides/docker-integration-testing.md | | |

### Phase 6: Performance Validation

- GOAL-006: Validate all performance targets are met under stable conditions

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-035 | Run test_listener_polling_throughput and verify >= 10 states/second | | |
| TASK-036 | Run test_inference_latency and verify < 100ms per decision | | |
| TASK-037 | Run test_actor_reflex_latency and verify < 10ms per reflex action | | |
| TASK-038 | Run test_observation_extraction_performance and verify < 5ms per observation | | |
| TASK-039 | Run test_reward_calculation_performance and verify < 1ms per reward calculation | | |
| TASK-040 | Create performance dashboard (python/tests/performance_dashboard.py) showing all metrics with pass/fail status | | |
| TASK-041 | Run full test suite (116 unit + 16 integration) and generate comprehensive test report | | |

## 3. Alternatives

- **ALT-001**: Use native RimWorld Windows installation instead of Docker - Rejected: Requires Windows-specific setup, less portable, harder to automate in CI/CD
- **ALT-002**: Mock RimWorld server for integration tests - Rejected: Would not catch real connection/stability issues, defeats purpose of integration testing
- **ALT-003**: Use RimWorld's -quicktest mode for faster startup - Considered but uncertain: May skip mod initialization, needs testing
- **ALT-004**: Run multiple RimWorld instances for parallel testing - Deferred: Complex, high resource usage, tackle after single-instance stability proven
- **ALT-005**: Use VNC for graphical debugging - Considered: May help debug graphics errors but adds complexity, implement if headless issues persist

## 4. Dependencies

- **DEP-001**: Docker and Docker Compose installed on host system
- **DEP-002**: rimworld-data volume populated with RimWorld Linux installation (via setup-rimworld-volume.ps1)
- **DEP-003**: Python 3.11+ with uv package manager for running tests
- **DEP-004**: .NET 8.0 SDK for building C# mod code
- **DEP-005**: Xvfb (virtual X server) in Docker container for headless Unity support
- **DEP-006**: pytest and pytest-timeout plugins for test execution
- **DEP-007**: Harmony mod (brrainz.harmony) installed in RimWorld Mods directory

## 5. Files

- **FILE-001**: docker-compose.yml - Add health check, memory limits, restart policy to integration service
- **FILE-002**: RimworldMLBridge/TcpProtobufServer.cs - Add heartbeat, connection timeout, improved error handling
- **FILE-003**: RimworldMLBridge/RimworldMLBridge.cs - Ensure proper initialization order, add error boundaries
- **FILE-004**: python/client/connection.py - Implement auto-reconnect with exponential backoff
- **FILE-005**: python/client/listener.py - Add connection state monitoring and recovery
- **FILE-006**: python/client/spectator_client.py - Handle temporary disconnections gracefully
- **FILE-007**: python/tests/integration/test_full_system.py - Fix test_listener_thread_polling, add test_connection_recovery
- **FILE-008**: python/diagnostics/check_rimworld_health.py - New diagnostic script for health checks
- **FILE-009**: docker/wait-for-server.sh - New script to wait for RimWorld TCP server readiness
- **FILE-010**: docker/collect_logs.sh - New script to aggregate logs for diagnostics
- **FILE-011**: .github/workflows/integration-tests.yml - New CI/CD workflow for automated integration testing
- **FILE-012**: docs/guides/docker-integration-testing.md - New documentation for Docker setup and troubleshooting

## 6. Testing

- **TEST-001**: Run diagnostics script for 5 minutes, verify no disconnections occur
- **TEST-002**: Run test_listener_thread_polling 10 times consecutively, all must pass
- **TEST-003**: Run full integration test suite (16 tests) with timeout=120s, all must pass
- **TEST-004**: Run performance benchmarks and verify all targets met (>10 states/s, <100ms inference, <10ms reflex, <5ms observation, <1ms reward)
- **TEST-005**: Test connection recovery by killing RimWorld mid-test and verifying client reconnects within 10s
- **TEST-006**: Run long-running stability test for 30 minutes with continuous polling, verify no crashes
- **TEST-007**: Build Docker image from scratch and run full test suite to verify reproducibility
- **TEST-008**: Run unit tests (116) + integration tests (16) in CI/CD pipeline and verify all pass

## 7. Risks & Assumptions

- **RISK-001**: RimWorld headless mode may have inherent instability - Mitigation: Implement robust client-side recovery, monitor Unity logs
- **RISK-002**: Connection drops may be due to Unity garbage collection pauses - Mitigation: Increase connection timeout, add heartbeat detection
- **RISK-003**: Docker networking may introduce latency or packet loss - Mitigation: Use host networking mode for integration service if issues persist
- **RISK-004**: RimWorld may not support long-running headless sessions - Mitigation: Add periodic state reset or game reload after N minutes
- **RISK-005**: Graphics errors in headless mode may eventually crash Unity - Mitigation: Monitor for specific error patterns, potentially add null texture workarounds in mod
- **ASSUMPTION-001**: RimWorld server crashes/hangs are the root cause (not client bugs) - Validate with diagnostics before implementing fixes
- **ASSUMPTION-002**: TCP protocol is reliable for message delivery - Correct, but need to handle connection-level failures
- **ASSUMPTION-003**: Docker container has sufficient resources (CPU/memory) - Verify with Docker stats monitoring
- **ASSUMPTION-004**: rimworld-data volume contains valid RimWorld installation - Verified by checking for RimWorldLinux executable and Data directory
- **ASSUMPTION-005**: Harmony mod is compatible with headless mode - Likely true, but verify with isolated testing

## 8. Related Specifications / Further Reading

- [REAL_TIME_ARCHITECTURE_UPDATE.md](../docs/specs/REAL_TIME_ARCHITECTURE_UPDATE.md) - Hybrid Valve architecture and real-time requirements
- [TCP_PROTOBUF_IMPLEMENTATION.md](../docs/implementation/TCP_PROTOBUF_IMPLEMENTATION.md) - Current TCP+Protobuf implementation details
- [PHASE_IV_ARCHITECTURE.md](../docs/specs/PHASE_IV_ARCHITECTURE.md) - Phase IV Python client architecture
- [docker/README.md](../docker/README.md) - Docker setup instructions and troubleshooting
- [Unity Headless Mode Documentation](https://docs.unity3d.com/Manual/CommandLineArguments.html) - Unity command-line arguments
- [RimWorld Modding Documentation](https://rimworldwiki.com/wiki/Modding_Tutorials) - RimWorld mod development
- [Docker Health Check Documentation](https://docs.docker.com/engine/reference/builder/#healthcheck) - Implementing container health checks
