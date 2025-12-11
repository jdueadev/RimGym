# /// script
# dependencies = [
#   "grpcio-tools",
#   "protobuf",
# ]
# ///

"""
Script to generate Python protobuf files from the .proto definition
"""

import subprocess
import sys
from pathlib import Path


def main():
    # Get the project root directory
    script_dir = Path(__file__).parent
    # Navigate up from src/shared/python/src to src/shared/Protos
    proto_dir = script_dir.parent.parent / "Protos"
    proto_file = proto_dir / "rimgym.proto"

    if not proto_file.exists():
        print(f"Error: Proto file not found at {proto_file}")
        sys.exit(1)

    print(f"Generating Python protobuf files from {proto_file}")
    print(f"Output directory: {script_dir}")

    # Run protoc to generate Python files
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={script_dir}",
        str(proto_file),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error generating protobuf files:")
        print(result.stderr)
        sys.exit(1)

    print("Successfully generated the protobuf message file (no gRPC service stubs):")
    print(f"  - {script_dir / 'rimgym_pb2.py'}")
    print(
        "Note: gRPC service stubs (e.g., rimgym_pb2_grpc.py) are NOT generated. Only the protobuf message file is produced."
    )


if __name__ == "__main__":
    main()
