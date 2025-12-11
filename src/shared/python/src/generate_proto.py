# /// script
# dependencies = [
#   "subprocess",
#   "sys",
#   "pathlib",
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
    proto_dir = script_dir.parent / "Protos"
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
        f"--grpc_python_out={script_dir}",
        str(proto_file),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error generating protobuf files:")
        print(result.stderr)
        sys.exit(1)

    print("Successfully generated:")
    print(f"  - {script_dir / 'mlbridge_pb2.py'}")
    print(f"  - {script_dir / 'mlbridge_pb2_grpc.py'}")


if __name__ == "__main__":
    main()
