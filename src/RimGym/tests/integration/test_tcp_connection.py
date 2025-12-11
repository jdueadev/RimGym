"""
TCP+Protobuf client for RimWorld ML Bridge.
Replaces gRPC with a simple TCP socket using Protocol Buffers for serialization.
"""

import socket
import struct

import shared.python.src.mlbridge_pb2 as mlbridge_pb2


class MLBridgeClient:
    """Client for connecting to RimWorld ML Bridge via TCP+Protobuf"""

    def __init__(self, host="localhost", port=50051):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """Connect to the RimWorld server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"Connected to RimWorld ML Bridge at {self.host}:{self.port}")

    def disconnect(self):
        """Disconnect from the server"""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Disconnected from RimWorld")

    def _send_message(self, message):
        """Send a length-prefixed protobuf message"""
        # Serialize the message
        data = message.SerializeToString()
        # Send length prefix (4 bytes, big-endian)
        length = struct.pack(">I", len(data))
        self.socket.sendall(length + data)

    def _receive_message(self, message_type):
        """Receive a length-prefixed protobuf message"""
        # Read length prefix (4 bytes, big-endian)
        length_data = self._receive_exactly(4)
        length = struct.unpack(">I", length_data)[0]

        # Read message data
        data = self._receive_exactly(length)

        # Deserialize
        message = message_type()
        message.ParseFromString(data)
        return message

    def _receive_exactly(self, n):
        """Receive exactly n bytes from the socket"""
        data = b""
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data")
            data += chunk
        return data

    def query_state(self):
        """Query the current game state (Phase II: returns RichStateMessage)"""
        command = mlbridge_pb2.CommandMessage()
        command.type = mlbridge_pb2.CommandType.QUERY_STATE

        self._send_message(command)
        return self._receive_message(mlbridge_pb2.RichStateMessage)

    def step(self, ticks=60):
        """Advance the game by a number of ticks and get the new state (Phase II: returns RichStateMessage)"""
        command = mlbridge_pb2.CommandMessage()
        command.type = mlbridge_pb2.CommandType.STEP
        command.ticks_to_run = ticks

        self._send_message(command)
        return self._receive_message(mlbridge_pb2.RichStateMessage)

    def reset(self):
        """Reset the game (not yet implemented in C#)"""
        command = mlbridge_pb2.CommandMessage()
        command.type = mlbridge_pb2.CommandType.RESET

        self._send_message(command)
        return self._receive_message(mlbridge_pb2.RichStateMessage)


def main():
    """Test the TCP+Protobuf connection"""
    client = MLBridgeClient()

    try:
        print("Connecting to RimWorld...")
        client.connect()

        print("\n1. Querying initial state...")
        state = client.query_state()
        print(f"   Frame ID: {state.frame_id}")
        print(f"   Timestamp: {state.timestamp_ms}ms")
        print(f"   Is Ready: {state.is_ready}")
        print(f"   Status: {state.status_message}")

        if state.is_ready:
            # Access global state using getattr since 'global' is a Python keyword
            global_state = getattr(state, "global")
            if global_state and global_state.ByteSize() > 0:
                print(f"   Temperature: {global_state.temperature:.1f}°C")
                print(f"   Weather: {global_state.weather}")
                print(f"   Day: {global_state.day}, Year: {global_state.year}")

            print(f"\n   Colonists: {len(state.colonists)}")

            # Display rich colonist data (Phase II)
            for colonist in state.colonists:
                print(f"\n     === {colonist.name} (ID: {colonist.thing_id}) ===")
                print(
                    f"       Position: ({colonist.position.x:.1f}, {colonist.position.y:.1f}, {colonist.position.z:.1f})"
                )
                print(
                    f"       Health: {colonist.health_percent:.1%}, Mood: {colonist.mood_percent:.1%}"
                )
                print(
                    f"       Drafted: {colonist.is_drafted}, Downed: {colonist.is_downed}"
                )

                # Display current job
                if colonist.HasField("current_job"):
                    print(f"       Job: {colonist.current_job.def_name}")

                # Display skills (top 3 by level)
                if colonist.skills:
                    top_skills = sorted(
                        colonist.skills, key=lambda s: s.level, reverse=True
                    )[:3]
                    print("       Top Skills:")
                    for skill in top_skills:
                        passion_str = ""
                        if skill.passion == mlbridge_pb2.Passion.PASSION_MINOR:
                            passion_str = " +"
                        elif skill.passion == mlbridge_pb2.Passion.PASSION_MAJOR:
                            passion_str = " ++"
                        print(
                            f"         • {skill.def_name}: {skill.level}{passion_str}"
                        )

                # Display needs
                if colonist.needs:
                    print("       Needs:")
                    for need in colonist.needs:
                        if need.cur_level > 0:  # Only show needs with values
                            print(f"         • {need.def_name}: {need.cur_level:.1%}")

                # Display health capacities
                if colonist.capacities:
                    critical_caps = [
                        c for c in colonist.capacities if c.efficiency < 1.0
                    ]
                    if critical_caps:
                        print("       Health Issues:")
                        for cap in critical_caps:
                            print(f"         • {cap.label}: {cap.efficiency:.1%}")

        print("\n2. Stepping simulation forward 60 ticks...")
        state = client.step(60)
        print(f"   Frame ID after step: {state.frame_id}")
        print(f"   Status: {state.status_message}")

        print("\n3. Querying state again...")
        state = client.query_state()
        print(f"   Frame ID: {state.frame_id}")

        print("\n✓ Test successful!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
