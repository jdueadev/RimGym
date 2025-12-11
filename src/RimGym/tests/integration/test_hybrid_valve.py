#!/usr/bin/env python3
"""
Phase III Test: Hybrid Valve - Training vs Inference Mode
Tests mode switching, tick control, and async state queries
"""

import socket
import struct
import sys
import time
from pathlib import Path

# Add parent directory to path to import protobuf bindings
sys.path.insert(0, str(Path(__file__).parent))

try:
    import shared.python.src.mlbridge_pb2 as pb
except ImportError:
    print("Error: mlbridge_pb2.py not found. Run generate_proto.py first:")
    print("  uv run python generate_proto.py")
    sys.exit(1)


class HybridValveClient:
    """TCP client for testing Hybrid Valve functionality"""

    def __init__(self, host="localhost", port=50051):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        """Connect to RimWorld ML Bridge server"""
        print(f"Connecting to {self.host}:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print("✅ Connected!")

    def send_command(self, command):
        """Send a protobuf command and receive response"""
        # Serialize to bytes
        data = command.SerializeToString()

        # Send length prefix (4 bytes, big-endian) + data
        length = struct.pack(">I", len(data))
        self.sock.sendall(length + data)

        # Read response length
        length_bytes = self.sock.recv(4)
        if not length_bytes:
            raise ConnectionError("Connection closed by server")

        response_length = struct.unpack(">I", length_bytes)[0]

        # Read response data
        response_data = b""
        while len(response_data) < response_length:
            chunk = self.sock.recv(response_length - len(response_data))
            if not chunk:
                raise ConnectionError("Connection closed while reading response")
            response_data += chunk

        # Deserialize response
        response = pb.RichStateMessage()
        response.ParseFromString(response_data)
        return response

    def set_mode(self, mode):
        """Switch between training and inference modes"""
        cmd = pb.CommandMessage()
        cmd.type = pb.CommandType.SET_MODE
        cmd.mode = mode

        mode_str = "TRAINING" if mode == pb.ExecutionMode.MODE_TRAINING else "INFERENCE"
        print(f"\n🔄 Setting mode to: {mode_str}")

        response = self.send_command(cmd)
        print(f"   Status: {response.status_message}")
        print(f"   Current Mode: {pb.ExecutionMode.Name(response.current_mode)}")
        return response

    def query_state(self):
        """Query current game state without advancing"""
        cmd = pb.CommandMessage()
        cmd.type = pb.CommandType.QUERY_STATE

        response = self.send_command(cmd)
        return response

    def step(self, ticks=60, wait_for_completion=True):
        """Advance simulation by N ticks (only works in training mode)"""
        cmd = pb.CommandMessage()
        cmd.type = pb.CommandType.STEP
        cmd.ticks_to_run = ticks

        print(f"\n⏭️  Sending STEP command ({ticks} ticks)...")
        start_time = time.time()

        # Send STEP command
        response = self.send_command(cmd)
        initial_frame = response.frame_id

        print(f"   Status: {response.status_message}")
        print(f"   Initial Frame: {initial_frame}")

        # In training mode, wait for ticks to complete
        if wait_for_completion and "Training Mode" in response.status_message:
            print(f"   Waiting for {ticks} ticks to complete...")

            max_wait = 10  # 10 seconds timeout
            poll_interval = 0.05  # 50ms polling
            waited = 0

            while waited < max_wait:
                time.sleep(poll_interval)
                waited += poll_interval

                # Poll current state
                current = self.query_state()
                ticks_advanced = current.frame_id - initial_frame

                if ticks_advanced >= ticks:
                    elapsed = time.time() - start_time
                    print(f"   ✅ Completed in {elapsed * 1000:.0f}ms")
                    print(f"   Final Frame: {current.frame_id}")
                    return current

            # Timeout
            print(f"   ⚠️  Timeout after {max_wait}s")
            return self.query_state()
        else:
            elapsed = time.time() - start_time
            print(f"   Response time: {elapsed * 1000:.1f}ms")
            return response

    def close(self):
        """Close connection"""
        if self.sock:
            self.sock.close()
            print("\n❌ Disconnected")


def print_state_info(state, show_velocity=False):
    """Print detailed state information"""
    print("\n📊 Game State:")
    print(f"   Frame ID: {state.frame_id}")
    print(f"   Delta Time: {state.delta_time_ms:.1f}ms")
    print(f"   Mode: {pb.ExecutionMode.Name(state.current_mode)}")
    print(f"   Is Delta: {state.is_delta}")
    print(f"   Colonists: {len(state.colonists)}")

    if state.colonists and show_velocity:
        print("\n👤 First Colonist:")
        c = state.colonists[0]
        print(f"   Name: {c.name}")
        print(f"   Position: ({c.position.x:.1f}, {c.position.y:.1f})")
        print(f"   Velocity: ({c.velocity.x:.2f}, {c.velocity.y:.2f}) units/sec")
        print(f"   Health: {c.health_percent * 100:.0f}%")


def test_training_mode(client):
    """Test synchronous training mode"""
    print("\n" + "=" * 60)
    print("TEST 1: Training Mode (Synchronous)")
    print("=" * 60)

    # Switch to training mode
    client.set_mode(pb.ExecutionMode.MODE_TRAINING)
    time.sleep(0.5)

    # Query initial state
    print("\n📍 Querying initial state...")
    state1 = client.query_state()
    print_state_info(state1)
    frame1 = state1.frame_id

    # Send STEP command - should advance exactly 60 ticks
    state2 = client.step(60)
    frame2 = state2.frame_id

    # Verify frame advanced
    ticks_advanced = frame2 - frame1
    print("\n✅ Verification:")
    print(f"   Frame before: {frame1}")
    print(f"   Frame after: {frame2}")
    print(f"   Ticks advanced: {ticks_advanced}")

    if ticks_advanced == 60:
        print("   ✅ PASS: Exact tick control verified!")
    else:
        print(f"   ❌ FAIL: Expected 60 ticks, got {ticks_advanced}")

    # Query again - frame should NOT have advanced (no STEP sent)
    time.sleep(0.1)
    state3 = client.query_state()
    frame3 = state3.frame_id

    if frame3 == frame2:
        print("   ✅ PASS: Game properly paused between steps")
    else:
        print(f"   ❌ FAIL: Game advanced without STEP (frame {frame2} → {frame3})")


def test_inference_mode(client):
    """Test asynchronous inference mode"""
    print("\n" + "=" * 60)
    print("TEST 2: Inference Mode (Asynchronous)")
    print("=" * 60)

    # Switch to inference mode
    client.set_mode(pb.ExecutionMode.MODE_INFERENCE)
    time.sleep(0.5)

    # Query initial state
    print("\n📍 Querying state at T0...")
    state1 = client.query_state()
    print_state_info(state1)
    frame1 = state1.frame_id

    # Wait and query again - game should have advanced on its own
    print("\n⏱️  Waiting 2 seconds...")
    time.sleep(2.0)

    print("\n📍 Querying state at T+2s...")
    state2 = client.query_state()
    print_state_info(state2, show_velocity=True)
    frame2 = state2.frame_id

    ticks_advanced = frame2 - frame1
    print("\n✅ Verification:")
    print(f"   Frame at T0: {frame1}")
    print(f"   Frame at T+2s: {frame2}")
    print(f"   Ticks advanced: {ticks_advanced}")

    # At normal speed (60 FPS), 2 seconds = ~120 ticks
    # Allow wide range since game speed can vary
    if ticks_advanced > 10:
        print("   ✅ PASS: Game running asynchronously")
    else:
        print("   ❌ FAIL: Game not advancing in inference mode")

    # Try STEP command - should be ignored
    print("\n⏭️  Attempting STEP in inference mode (should be ignored)...")
    state3 = client.step(60)
    print(f"   {state3.status_message}")


def test_velocity_tracking(client):
    """Test velocity vector calculation"""
    print("\n" + "=" * 60)
    print("TEST 3: Velocity Tracking")
    print("=" * 60)

    # Ensure in inference mode for continuous motion
    client.set_mode(pb.ExecutionMode.MODE_INFERENCE)
    time.sleep(0.5)

    # Query multiple times to build velocity history
    print("\n📍 Sampling colonist positions over 3 seconds...")

    samples = []
    for i in range(4):
        state = client.query_state()
        if state.colonists:
            c = state.colonists[0]
            samples.append(
                {
                    "time": state.timestamp_ms,
                    "position": (c.position.x, c.position.y),
                    "velocity": (c.velocity.x, c.velocity.y),
                    "delta_time": state.delta_time_ms,
                }
            )
            print(
                f"   Sample {i + 1}: pos=({c.position.x:.1f}, {c.position.y:.1f}), "
                f"vel=({c.velocity.x:.2f}, {c.velocity.y:.2f})"
            )

        if i < 3:
            time.sleep(1.0)

    print("\n✅ Verification:")
    if len(samples) >= 2:
        # Check if velocity vectors are non-zero (colonist moving)
        has_motion = any(
            abs(s["velocity"][0]) > 0.01 or abs(s["velocity"][1]) > 0.01
            for s in samples
        )

        if has_motion:
            print("   ✅ PASS: Velocity vectors tracked (colonist moving)")
        else:
            print("   ℹ️  INFO: No movement detected (colonists idle)")

        # Check delta_time is reasonable
        avg_dt = sum(s["delta_time"] for s in samples[1:]) / (len(samples) - 1)
        print(f"   Average delta time: {avg_dt:.0f}ms")

        if 50 < avg_dt < 5000:  # Between 50ms and 5s
            print("   ✅ PASS: Delta time tracking working")
        else:
            print("   ⚠️  WARN: Delta time outside expected range")


def main():
    """Run all Phase III tests"""
    print("=" * 60)
    print("Phase III: Hybrid Valve Test Suite")
    print("=" * 60)
    print("\nThis tests:")
    print("  1. Training mode (synchronous tick control)")
    print("  2. Inference mode (asynchronous game flow)")
    print("  3. Velocity tracking for position extrapolation")
    print("\nMake sure RimWorld is running with a loaded save!")

    input("\nPress Enter to begin tests...")

    client = HybridValveClient()

    try:
        client.connect()

        # Run test suite
        test_training_mode(client)
        test_inference_mode(client)
        test_velocity_tracking(client)

        print("\n" + "=" * 60)
        print("✅ All tests complete!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    main()
