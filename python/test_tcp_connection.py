"""
TCP+Protobuf client for RimWorld ML Bridge.
Replaces gRPC with a simple TCP socket using Protocol Buffers for serialization.
"""

import socket
import struct

import mlbridge_pb2


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
        """Query the current game state"""
        command = mlbridge_pb2.CommandMessage()
        command.type = mlbridge_pb2.CommandType.QUERY_STATE

        self._send_message(command)
        return self._receive_message(mlbridge_pb2.StateMessage)

    def step(self, ticks=60):
        """Advance the game by a number of ticks and get the new state"""
        command = mlbridge_pb2.CommandMessage()
        command.type = mlbridge_pb2.CommandType.STEP
        command.ticks_to_run = ticks

        self._send_message(command)
        return self._receive_message(mlbridge_pb2.StateMessage)

    def reset(self):
        """Reset the game (not yet implemented in C#)"""
        command = mlbridge_pb2.CommandMessage()
        command.type = mlbridge_pb2.CommandType.RESET

        self._send_message(command)
        return self._receive_message(mlbridge_pb2.StateMessage)


def main():
    """Test the TCP+Protobuf connection"""
    client = MLBridgeClient()

    try:
        print("Connecting to RimWorld...")
        client.connect()

        print("\n1. Querying initial state...")
        state = client.query_state()
        print(f"   Frame ID: {state.frame_id}")
        print(f"   Is Ready: {state.is_ready}")
        print(f"   Status: {state.status_message}")

        if state.is_ready:
            # Access global state using getattr since 'global' is a Python keyword
            global_state = getattr(state, "global")
            if global_state and global_state.ByteSize() > 0:
                print(f"   Temperature: {global_state.temperature:.1f}°C")
                print(f"   Weather: {global_state.weather}")
                print(f"   Day: {global_state.day}, Year: {global_state.year}")

            print(f"   Colonists: {len(state.entities)}")

            for entity in state.entities:
                print(f"     - {entity.def_name} (ID: {entity.id})")
                print(
                    f"       Position: ({entity.position.x}, {entity.position.y}, {entity.position.z})"
                )
                print(f"       Health: {entity.state.health:.1%}")
                print(f"       Job: {entity.state.current_job}")

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
