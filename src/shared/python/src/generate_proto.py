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
    script_dir = Path(__file__).resolve().parent
    # Navigate up from src/shared/python/src to src/shared/Protos
    shared_dir = script_dir.parent.parent
    proto_dir = shared_dir / "Protos"
    proto_file = proto_dir / "rimgym.proto"

    if not proto_file.exists():
        print(f"Error: Proto file not found at {proto_file}", file=sys.stderr)
        return 1

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
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except subprocess.CalledProcessError as ex:
        print("Error generating protobuf files:", file=sys.stderr)
        if ex.stdout:
            print(ex.stdout, file=sys.stderr)
        if ex.stderr:
            print(ex.stderr, file=sys.stderr)
        return ex.returncode

    print("Successfully generated:")
    print(f"  - {script_dir / 'rimgym_pb2.py'}")
    print("Note: This generates protobuf messages only (no gRPC stubs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
