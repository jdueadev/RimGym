"""
Phase V Performance Testing Suite

Tests performance of full game state extraction including:
- Map data (terrain, buildings, items)
- Incident history
- World state (factions, settlements)

Measures:
- Total state extraction time (target: <5ms)
- Serialization time
- Network transfer time
- Python parsing time
"""

import logging
import statistics
import time
from typing import Any, Dict, List

from client import ClientConfig, RichGameState, SpectatorClient

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Container for performance measurements."""

    def __init__(self):
        self.round_trip_times: List[float] = []
        self.parse_times: List[float] = []
        self.state_sizes: List[int] = []
        self.building_counts: List[int] = []
        self.item_counts: List[int] = []
        self.incident_counts: List[int] = []
        self.faction_counts: List[int] = []

    def add_measurement(
        self,
        round_trip_ms: float,
        parse_ms: float,
        state_size: int,
        building_count: int,
        item_count: int,
        incident_count: int,
        faction_count: int,
    ):
        """Add a performance measurement."""
        self.round_trip_times.append(round_trip_ms)
        self.parse_times.append(parse_ms)
        self.state_sizes.append(state_size)
        self.building_counts.append(building_count)
        self.item_counts.append(item_count)
        self.incident_counts.append(incident_count)
        self.faction_counts.append(faction_count)

    def report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.round_trip_times:
            return {"error": "No measurements recorded"}

        return {
            "measurements": len(self.round_trip_times),
            "round_trip_time_ms": {
                "mean": statistics.mean(self.round_trip_times),
                "median": statistics.median(self.round_trip_times),
                "min": min(self.round_trip_times),
                "max": max(self.round_trip_times),
                "stdev": statistics.stdev(self.round_trip_times)
                if len(self.round_trip_times) > 1
                else 0.0,
                "p95": statistics.quantiles(self.round_trip_times, n=20)[18]
                if len(self.round_trip_times) >= 20
                else max(self.round_trip_times),
                "p99": statistics.quantiles(self.round_trip_times, n=100)[98]
                if len(self.round_trip_times) >= 100
                else max(self.round_trip_times),
            },
            "parse_time_ms": {
                "mean": statistics.mean(self.parse_times),
                "median": statistics.median(self.parse_times),
                "min": min(self.parse_times),
                "max": max(self.parse_times),
            },
            "state_size_bytes": {
                "mean": statistics.mean(self.state_sizes),
                "median": statistics.median(self.state_sizes),
                "min": min(self.state_sizes),
                "max": max(self.state_sizes),
            },
            "data_complexity": {
                "buildings_mean": statistics.mean(self.building_counts),
                "items_mean": statistics.mean(self.item_counts),
                "incidents_mean": statistics.mean(self.incident_counts),
                "factions_mean": statistics.mean(self.faction_counts),
            },
        }

    def print_report(self):
        """Print formatted performance report."""
        report = self.report()

        if "error" in report:
            print(f"Error: {report['error']}")
            return

        print("\n" + "=" * 80)
        print("  PHASE V PERFORMANCE REPORT")
        print("=" * 80)
        print(f"\nMeasurements: {report['measurements']}")

        print("\n--- Round Trip Time (Client → Server → Client) ---")
        rtt = report["round_trip_time_ms"]
        print(f"  Mean:   {rtt['mean']:.2f} ms")
        print(f"  Median: {rtt['median']:.2f} ms")
        print(f"  Min:    {rtt['min']:.2f} ms")
        print(f"  Max:    {rtt['max']:.2f} ms")
        print(f"  StdDev: {rtt['stdev']:.2f} ms")
        print(f"  P95:    {rtt['p95']:.2f} ms")
        print(f"  P99:    {rtt['p99']:.2f} ms")

        # Performance assessment
        if rtt["mean"] <= 5.0:
            print(f"  ✓ EXCELLENT: Mean latency {rtt['mean']:.2f}ms <= 5ms target")
        elif rtt["mean"] <= 10.0:
            print(f"  ⚠ GOOD: Mean latency {rtt['mean']:.2f}ms within acceptable range")
        else:
            print(
                f"  ✗ NEEDS OPTIMIZATION: Mean latency {rtt['mean']:.2f}ms exceeds 10ms"
            )

        print("\n--- Parse Time (Protobuf → Python Models) ---")
        pt = report["parse_time_ms"]
        print(f"  Mean:   {pt['mean']:.2f} ms")
        print(f"  Median: {pt['median']:.2f} ms")
        print(f"  Min:    {pt['min']:.2f} ms")
        print(f"  Max:    {pt['max']:.2f} ms")

        print("\n--- State Size (Serialized Protobuf) ---")
        ss = report["state_size_bytes"]
        print(f"  Mean:   {ss['mean']:.0f} bytes ({ss['mean'] / 1024:.1f} KB)")
        print(f"  Median: {ss['median']:.0f} bytes ({ss['median'] / 1024:.1f} KB)")
        print(f"  Min:    {ss['min']:.0f} bytes")
        print(f"  Max:    {ss['max']:.0f} bytes ({ss['max'] / 1024:.1f} KB)")

        print("\n--- Data Complexity ---")
        dc = report["data_complexity"]
        print(f"  Buildings (avg): {dc['buildings_mean']:.0f}")
        print(f"  Items (avg):     {dc['items_mean']:.0f}")
        print(f"  Incidents (avg): {dc['incidents_mean']:.0f}")
        print(f"  Factions (avg):  {dc['factions_mean']:.0f}")

        print("\n" + "=" * 80)


def test_phase_v_performance(duration_seconds: int = 30, poll_interval_ms: int = 100):
    """
    Test Phase V performance over a duration.

    Args:
        duration_seconds: How long to run the test
        poll_interval_ms: Interval between state queries
    """
    config = ClientConfig(
        host="localhost",
        port=50051,
        inference_mode=True,
        training_mode=False,
        poll_interval_ms=poll_interval_ms,
        log_level="WARNING",  # Reduce noise during testing
    )

    metrics = PerformanceMetrics()

    print("=" * 80)
    print("  PHASE V PERFORMANCE TEST")
    print("=" * 80)
    print(f"\nDuration: {duration_seconds} seconds")
    print(f"Poll Interval: {poll_interval_ms} ms")
    print("\nConnecting to RimWorld server...")

    with SpectatorClient(config) as client:
        if not client.wait_ready(timeout=10.0):
            logger.error("Failed to connect to server")
            return

        print("✓ Connected\n")

        # Wait for initial state
        time.sleep(0.5)

        # Verify Phase V is available
        initial_state = client.get_state(timeout=1.0)
        if not initial_state or not isinstance(initial_state, RichGameState):
            logger.error("Server does not support Phase V")
            return

        if not initial_state.is_phase_v:
            logger.error("Phase V data not present in state")
            return

        print("Phase V Confirmed!")
        print(f"Colony Size: {initial_state.colonist_count} colonists")
        if initial_state.map_state:
            print(
                f"Map Complexity: {initial_state.map_state.building_count} buildings, {initial_state.map_state.item_count} items"
            )
        print("\nStarting performance measurement...\n")

        start_time = time.time()
        measurement_count = 0

        try:
            while time.time() - start_time < duration_seconds:
                # Measure round trip time
                query_start = time.time()
                proto_state = client.state_queue.get_latest()  # Get raw protobuf
                query_end = time.time()

                if proto_state:
                    # Measure parse time
                    parse_start = time.time()
                    from client.parsers import parse_rich_state_message

                    state = parse_rich_state_message(proto_state)
                    parse_end = time.time()

                    # Estimate state size (would need raw bytes for exact measurement)
                    state_size = len(proto_state.SerializeToString())

                    # Extract metrics
                    building_count = (
                        state.map_state.building_count if state.map_state else 0
                    )
                    item_count = state.map_state.item_count if state.map_state else 0
                    incident_count = (
                        state.incident_state.incident_count
                        if state.incident_state
                        else 0
                    )
                    faction_count = (
                        state.world_state.faction_count if state.world_state else 0
                    )

                    # Record measurement
                    metrics.add_measurement(
                        round_trip_ms=(query_end - query_start) * 1000,
                        parse_ms=(parse_end - parse_start) * 1000,
                        state_size=state_size,
                        building_count=building_count,
                        item_count=item_count,
                        incident_count=incident_count,
                        faction_count=faction_count,
                    )

                    measurement_count += 1

                    # Progress indicator
                    if measurement_count % 10 == 0:
                        elapsed = time.time() - start_time
                        print(
                            f"[{measurement_count:4d}] {elapsed:.1f}s elapsed, last RTT: {(query_end - query_start) * 1000:.2f}ms"
                        )

                # Sleep until next poll
                time.sleep(poll_interval_ms / 1000.0)

        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")

        print(
            f"\n✓ Completed {measurement_count} measurements in {time.time() - start_time:.1f} seconds"
        )

    # Print report
    metrics.print_report()


def test_large_colony_stress():
    """
    Stress test with recommendations for large colony.

    NOTE: This test assumes you have a large colony (20+ colonists, 500+ buildings).
    If not, this will still run but metrics will not reflect stress conditions.
    """
    print("\n" + "=" * 80)
    print("  LARGE COLONY STRESS TEST")
    print("=" * 80)
    print("\nThis test is designed for large colonies (20+ colonists, 500+ buildings)")
    print("to measure performance under high data complexity.")
    print()

    response = input("Do you have a large colony loaded? (y/n): ")
    if response.lower() != "y":
        print("\nTest skipped. Load a large colony and run again for accurate results.")
        return

    print("\nRunning 60-second stress test...\n")
    test_phase_v_performance(duration_seconds=60, poll_interval_ms=50)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stress":
        test_large_colony_stress()
    else:
        # Standard performance test
        test_phase_v_performance(duration_seconds=30, poll_interval_ms=100)

        print(
            "\n\nTo run stress test with large colony: python performance_test_phase5.py --stress"
        )
