import grpc
import time
import sys
from pathlib import Path

# Add the generated protobuf files to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import mlbridge_pb2
    import mlbridge_pb2_grpc
except ImportError as e:
    print(f"Error importing generated protobuf files: {e}")
    print("Please run: python -m grpc_tools.protoc -I../Protos --python_out=. --grpc_python_out=. ../Protos/mlbridge.proto")
    sys.exit(1)

def main():
    host = 'localhost'
    port = 50051
    max_retries = 30
    retry_delay = 2  # seconds

    print(f"RimWorld ML Bridge gRPC Test Client")
    print(f"=" * 40)
    print(f"Target: {host}:{port}")
    print(f"")
    print(f"Make sure:")
    print(f"  1. RimWorld is running")
    print(f"  2. The MLBridge mod is enabled")
    print(f"  3. You've loaded into a game (not just main menu)")
    print(f"")

    # Create gRPC channel
    channel = grpc.insecure_channel(f'{host}:{port}')
    stub = mlbridge_pb2_grpc.MLBridgeStub(channel)

    # Retry loop
    for attempt in range(1, max_retries + 1):
        print(f"Connection attempt {attempt}/{max_retries}...")
        try:
            # Try to get state to test connection
            response = stub.GetState(mlbridge_pb2.EmptyMessage(), timeout=5)
            print(f"Connected successfully!")
            print(f"Initial state: {response.status_message}")
            break
        except grpc.RpcError as e:
            print(f"  Connection failed: {e.code()}")
            if attempt < max_retries:
                print(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"\nFailed to connect after {max_retries} attempts.")
                print(f"Check RimWorld's Player.log for [MLBridge] messages.")
                sys.exit(1)
        except Exception as e:
            print(f"  Unexpected error: {e}")
            sys.exit(1)

    # Main interaction loop
    print(f"\nInteracting with game via gRPC...")
    print(f"-" * 40)

    try:
        tick_num = 0
        while True:
            # Get current game state
            state = stub.GetState(mlbridge_pb2.EmptyMessage())
            print(f"\n[Frame {state.frame_id}] Status: {state.status_message}")
            
            if state.is_ready and state.HasField('global'):
                print(f"  Day {state.global.day}, Year {state.global.year}")
                print(f"  Temperature: {state.global.temperature:.1f}°C")
                print(f"  Entities: {len(state.entities)}")
                
                # Print entity details
                for entity in state.entities:
                    print(f"    - {entity.def_name} (ID: {entity.id})")
                    if entity.HasField('state'):
                        print(f"      Health: {entity.state.health:.1%}, Job: {entity.state.current_job}")
            
            # Send a tick acknowledgment
            tick_num += 1
            ack = stub.SendTick(mlbridge_pb2.TickMessage(
                tick_count=tick_num,
                frame_id=state.frame_id
            ))
            
            if ack.success:
                print(f"  Tick {ack.tick_count} acknowledged")
            
            # Execute a simple command
            cmd_response = stub.ExecuteCommand(mlbridge_pb2.CommandMessage(
                type=mlbridge_pb2.NO_OP,
                ticks_to_run=0
            ))
            print(f"  Command result: {cmd_response.status_message}")
            
            # Wait before next poll
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\nDisconnected by user (Ctrl+C)")
    finally:
        channel.close()

if __name__ == "__main__":
    main()
