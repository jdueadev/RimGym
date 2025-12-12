"""
Automated Test Suite for RimWorld ML Bridge - Phase III Hybrid Valve

This script automates the full testing process:
1. Launches RimWorld with dev mode quicktest
2. Waits for connection
3. Runs tests at each speed: Paused, 1x, 2x, 3x
4. Closes RimWorld
5. Generates test report

Requirements:
- RimWorld installed with mod loaded
- Environment variable RIMWORLD_PATH set to RimWorld installation directory
- Save file for quick loading (or use -quicktest)

Usage:
    python test_automated_suite.py [--rimworld-path PATH] [--no-launch] [--no-close]
"""

import argparse
import os
import socket
import struct
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import shared.python.src.mlbridge_pb2 as mlbridge_pb2
import shared.python.src.rimgym_pb2 as rimgym_pb2


class AutomatedTestClient:
    """Client for automated testing with game speed control"""

    def __init__(self, host="localhost", port=50051):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self, timeout=60, retry_interval=2):
        """Connect with retry logic for game startup"""
        print(f"🔄 Waiting for RimWorld to start (timeout: {timeout}s)...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                print("✅ Connected to RimWorld!")
                return True
            except (ConnectionRefusedError, OSError):
                time.sleep(retry_interval)
                elapsed = int(time.time() - start_time)
                print(f"   Waiting... ({elapsed}s elapsed)", end="\r")

        print(f"\n❌ Connection timeout after {timeout}s")
        return False

    def disconnect(self):
        """Close connection"""
        if self.sock:
            self.sock.close()
            self.sock = None

    def send_command(self, command):
        """Send command and receive response"""
        # Serialize
        data = command.SerializeToString()

        # Send with length prefix (big-endian)
        length = struct.pack(">I", len(data))
        self.sock.sendall(length + data)

        # Receive length prefix
        length_data = self._recv_exactly(4)
        length = struct.unpack(">I", length_data)[0]

        # Receive message
        response_data = self._recv_exactly(length)
        response = rimgym_pb2.RichStateMessage()
        response.ParseFromString(response_data)

        return response

    def _recv_exactly(self, n):
        """Receive exactly n bytes"""
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data

    def set_mode(self, mode):
        """Set execution mode"""
        cmd = rimgym_pb2.CommandMessage(type=rimgym_pb2.SET_MODE, mode=mode)
        response = self.send_command(cmd)
        return response

    def set_speed(self, speed):
        """Set game speed"""
        cmd = mlbridge_pb2.CommandMessage(type=mlbridge_pb2.SET_SPEED, speed=speed)
        response = self.send_command(cmd)
        return response

    def step(self, ticks=60, timeout=10.0, poll_interval=0.05):
        """Send STEP command and wait for completion"""
        cmd = mlbridge_pb2.CommandMessage(type=mlbridge_pb2.STEP, ticks_to_run=ticks)

        initial_state = self.send_command(cmd)
        initial_frame = initial_state.frame_id
        start_time = time.time()

        # Poll until ticks complete or timeout
        while time.time() - start_time < timeout:
            time.sleep(poll_interval)
            state = self.query_state()

            if state.frame_id >= initial_frame + ticks:
                elapsed_ms = int((time.time() - start_time) * 1000)
                return state, elapsed_ms

        raise TimeoutError(f"STEP did not complete within {timeout}s")

    def query_state(self):
        """Query current state"""
        cmd = mlbridge_pb2.CommandMessage(type=mlbridge_pb2.QUERY_STATE)
        return self.send_command(cmd)

    def wait_for_game_ready(self, timeout=120, poll_interval=2):
        """Wait for game to be fully loaded and ready"""
        print(f"⏳ Waiting for game to load (timeout: {timeout}s)...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                state = self.query_state()

                # Check if game is ready (has colonists means map is loaded)
                if state.is_ready and len(state.colonists) > 0:
                    elapsed = int(time.time() - start_time)
                    print(f"✅ Game ready! (took {elapsed}s)")
                    print(f"   Map loaded with {len(state.colonists)} colonists")
                    return True

                # Show progress
                elapsed = int(time.time() - start_time)
                status = state.status_message if state.status_message else "Loading..."
                print(f"   {status} ({elapsed}s elapsed)", end="\r")

                time.sleep(poll_interval)

            except Exception:
                # Connection might be unstable during loading
                time.sleep(poll_interval)
                continue

        print(f"\n❌ Game did not load within {timeout}s")
        return False


def launch_rimworld(rimworld_path, quicktest=True):
    """Launch RimWorld in dev mode with quicktest"""
    exe_path = Path(rimworld_path) / "RimWorldWin64.exe"

    if not exe_path.exists():
        raise FileNotFoundError(f"RimWorld not found at: {exe_path}")

    print(f"🚀 Launching RimWorld from: {rimworld_path}")

    # Build command with dev mode and quicktest
    cmd = [str(exe_path)]
    if quicktest:
        cmd.append("-quicktest")

    # Launch detached process
    process = subprocess.Popen(
        cmd,
        cwd=str(exe_path.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        if sys.platform == "win32"
        else 0,
    )

    print(f"   Process ID: {process.pid}")
    return process


def run_speed_test(
    client, speed_name, speed_enum, expected_min_ticks, expected_max_ticks
):
    """Run test at specific speed"""
    print(f"\n{'=' * 60}")
    print(f"TEST: {speed_name}")
    print(f"{'=' * 60}")

    results = {
        "speed": speed_name,
        "success": False,
        "error": None,
        "training_ticks": None,
        "training_time_ms": None,
        "inference_ticks": None,
        "inference_time_ms": None,
    }

    try:
        # Set speed
        print(f"🎛️  Setting speed to: {speed_name}")
        response = client.set_speed(speed_enum)
        print(f"   Status: {response.status_message}")

        # Test Training Mode
        print("\n📍 Testing Training Mode...")
        client.set_mode(mlbridge_pb2.MODE_TRAINING)

        before = client.query_state()
        state, elapsed_ms = client.step(60)
        after_frame = state.frame_id

        ticks_advanced = after_frame - before.frame_id
        results["training_ticks"] = ticks_advanced
        results["training_time_ms"] = elapsed_ms

        print(f"   ✅ Training: {ticks_advanced} ticks in {elapsed_ms}ms")

        if ticks_advanced != 60:
            results["error"] = f"Training mode: Expected 60 ticks, got {ticks_advanced}"
            print(f"   ❌ {results['error']}")
            return results

        # Test Inference Mode
        print("\n📍 Testing Inference Mode...")
        client.set_mode(mlbridge_pb2.MODE_INFERENCE)

        before = client.query_state()
        time.sleep(2.0)
        after = client.query_state()

        ticks_advanced = after.frame_id - before.frame_id
        elapsed_ms = int(after.delta_time_ms)
        results["inference_ticks"] = ticks_advanced
        results["inference_time_ms"] = elapsed_ms

        print(f"   ✅ Inference: {ticks_advanced} ticks in {elapsed_ms}ms")

        # Validate tick count is in expected range
        if speed_name != "Paused":  # Paused should have 0 ticks
            if not (expected_min_ticks <= ticks_advanced <= expected_max_ticks):
                results["error"] = (
                    f"Inference mode: Expected {expected_min_ticks}-{expected_max_ticks} ticks, got {ticks_advanced}"
                )
                print(f"   ⚠️  {results['error']}")

        results["success"] = True

    except Exception as e:
        results["error"] = str(e)
        print(f"   ❌ Error: {e}")

    return results


def run_full_suite(client):
    """Run complete test suite at all speeds"""
    print("\n" + "=" * 60)
    print("AUTOMATED TEST SUITE - Phase III Hybrid Valve")
    print("=" * 60)

    # Wait for game to be fully loaded before running tests
    if not client.wait_for_game_ready(timeout=120):
        print("\n❌ Cannot run tests: Game not ready")
        return []

    # Test configurations: (name, enum, min_ticks, max_ticks)
    speeds = [
        ("Paused", mlbridge_pb2.SPEED_PAUSED, 0, 0),
        ("1x Speed", mlbridge_pb2.SPEED_NORMAL, 100, 140),  # ~120 expected
        ("2x Speed", mlbridge_pb2.SPEED_FAST, 250, 400),  # ~300 expected
        ("3x Speed", mlbridge_pb2.SPEED_SUPERFAST, 600, 800),  # ~720 expected
    ]

    results = []

    for speed_name, speed_enum, min_ticks, max_ticks in speeds:
        result = run_speed_test(client, speed_name, speed_enum, min_ticks, max_ticks)
        results.append(result)
        time.sleep(0.5)  # Brief pause between tests

    return results


def generate_report(results, output_file=None):
    """Generate test report"""
    print("\n" + "=" * 60)
    print("TEST REPORT")
    print("=" * 60)
    if not results:
        print("❌ No tests were run")
        return False
    report_lines = []
    report_lines.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total Tests: {len(results)}")
    report_lines.append("")

    passed = sum(1 for r in results if r["success"] and not r["error"])
    failed = len(results) - passed

    report_lines.append(f"✅ Passed: {passed}")
    report_lines.append(f"❌ Failed: {failed}")
    report_lines.append("")
    report_lines.append("=" * 60)

    for result in results:
        status = "✅ PASS" if result["success"] and not result["error"] else "❌ FAIL"
        report_lines.append(f"\n{status} - {result['speed']}")

        if result["training_ticks"] is not None:
            report_lines.append(
                f"  Training: {result['training_ticks']} ticks in {result['training_time_ms']}ms"
            )

        if result["inference_ticks"] is not None:
            report_lines.append(
                f"  Inference: {result['inference_ticks']} ticks in {result['inference_time_ms']}ms"
            )

        if result["error"]:
            report_lines.append(f"  Error: {result['error']}")

    report_lines.append("\n" + "=" * 60)

    report_text = "\n".join(report_lines)
    print(report_text)

    if output_file:
        with open(output_file, "w") as f:
            f.write(report_text)
        print(f"\n📄 Report saved to: {output_file}")

    return passed == len(results)


def main():
    parser = argparse.ArgumentParser(
        description="Automated test suite for RimWorld ML Bridge"
    )
    parser.add_argument(
        "--rimworld-path", type=str, help="Path to RimWorld installation"
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Skip launching RimWorld (assume already running)",
    )
    parser.add_argument(
        "--no-close", action="store_true", help="Keep RimWorld open after tests"
    )
    parser.add_argument("--output", type=str, help="Output file for test report")

    args = parser.parse_args()

    # Determine RimWorld path
    rimworld_path = args.rimworld_path or os.environ.get("RIMWORLD_PATH")

    process = None

    try:
        # Launch RimWorld if requested
        if not args.no_launch:
            if not rimworld_path:
                print("❌ Error: RimWorld path not specified")
                print(
                    "   Set RIMWORLD_PATH environment variable or use --rimworld-path"
                )
                return 1

            process = launch_rimworld(rimworld_path)
            time.sleep(5)  # Give it a moment to start

        # Connect to game
        client = AutomatedTestClient()
        if not client.connect(timeout=90):
            return 1

        # Run test suite
        results = run_full_suite(client)

        # Generate report
        all_passed = generate_report(results, args.output)

        # Disconnect
        client.disconnect()

        # Close RimWorld if requested
        if process and not args.no_close:
            print("\n🛑 Closing RimWorld...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            print("   RimWorld closed")

        return 0 if all_passed else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        if process and not args.no_close:
            process.terminate()
        return 1

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        if process and not args.no_close:
            process.terminate()
        return 1


if __name__ == "__main__":
    sys.exit(main())
