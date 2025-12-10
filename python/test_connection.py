import socket
import time
import sys

def main():
    host = '127.0.0.1'
    port = 9876
    max_retries = 30
    retry_delay = 2  # seconds

    print(f"RimWorld ML Bridge Test Client")
    print(f"=" * 40)
    print(f"Target:  {host}:{port}")
    print(f"")
    print(f"Make sure:")
    print(f"  1. RimWorld is running")
    print(f"  2. The MLBridge mod is enabled")
    print(f"  3. You've loaded into a game (not just main menu)")
    print(f"")

    # Retry loop
    for attempt in range(1, max_retries + 1):
        print(f"Connection attempt {attempt}/{max_retries}...")
        try:
            sock = socket.socket(socket.AF_INET, socket. SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            print(f"Connected successfully!")
            break
        except ConnectionRefusedError:
            print(f"  Connection refused - server not ready yet")
            if attempt < max_retries:
                print(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"\nFailed to connect after {max_retries} attempts.")
                print(f"Check RimWorld's Player.log for [MLBridge] messages.")
                sys.exit(1)
        except socket.timeout:
            print(f"  Connection timed out")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"  Unexpected error: {e}")
            sys.exit(1)

    # Main communication loop
    print(f"\nListening for game ticks...")
    print(f"-" * 40)

    sock.settimeout(None)  # Remove timeout for normal operation
    buffer = ""

    try:
        while True:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("Connection closed by server")
                break

            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                print(f"<-- Received: {line}")

                if line.startswith("TICK:"):
                    tick = int(line.split(":")[1])
                    response = f"ACK:{tick}"
                    sock.sendall((response + "\n").encode('utf-8'))
                    print(f"--> Sent: {response}")

    except KeyboardInterrupt:
        print("\n\nDisconnected by user (Ctrl+C)")
    finally:
        sock. close()

if __name__ == "__main__":
    main()