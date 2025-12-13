#!/usr/bin/env python3
"""RimTCP reset smoke test.

Purpose:
- Minimal manual validation that RimTCP implements RESET as "load known save".
- Sends RESET (optionally with a save name), then polls QUERY_STATE until:
  - reset_in_progress == False
  - is_ready == True

Exit codes:
- 0: success
- 1: failure / timeout

Notes:
- Transport is raw TCP with a 4-byte big-endian length prefix + protobuf bytes.
- This script accepts either RichStateMessage or StateMessage responses.
"""

from __future__ import annotations

import argparse
import os
import socket
import struct
import sys
import time
from pathlib import Path
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 50051
DEFAULT_TIMEOUT_S = 2.0
DEFAULT_MAX_WAIT_S = 60.0
DEFAULT_POLL_INTERVAL_S = 0.5
MAX_RESPONSE_BYTES = 8 * 1024 * 1024  # 8 MiB


def _local_proto_paths() -> list[str]:
    here = Path(__file__).resolve()

    # Find repo root by walking upward until we see src/shared/python/src.
    repo_root: Path | None = None
    for parent in here.parents:
        if (parent / "src" / "shared" / "python" / "src").exists():
            repo_root = parent
            break

    candidates = [
        # Runtime/container layouts
        here.parent,
        here.parent.parent / "protos",
    ]

    # Repo/dev layout
    if repo_root is not None:
        candidates.append(repo_root / "src" / "shared" / "python" / "src")

    return [str(p) for p in candidates]


def _send_length_prefixed(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("connection closed")
        buf.extend(chunk)
    return bytes(buf)


def _recv_length_prefixed(sock: socket.socket) -> bytes:
    length_bytes = _recv_exact(sock, 4)
    length = struct.unpack(">I", length_bytes)[0]

    if length <= 0:
        raise ValueError("invalid response length")
    if length > MAX_RESPONSE_BYTES:
        raise ValueError("response too large")

    return _recv_exact(sock, length)


def _load_protos() -> Any:
    # Make a best effort to load protos regardless of how the script is run:
    # - repo root: rimgym_pb2.py lives at src/shared/python/src
    # - container images: may vendor protos alongside this script
    for p in _local_proto_paths():
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        import rimgym_pb2  # type: ignore

        return rimgym_pb2
    except ModuleNotFoundError as e:
        if e.name == "google":
            raise RuntimeError(
                "Missing protobuf runtime (google.protobuf). If you're using uv, run this via the RimGym project:\n"
                "  uv sync --project src/RimGym\n"
                "  uv run --project src/RimGym python src/RimGym/src/diagnostics/rimtcp_reset_smoketest.py ..."
            ) from e
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="RimTCP RESET smoke test")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--save-name",
        default=os.environ.get("RIMGYM_RESET_SAVE", ""),
        help="Optional save name to load (defaults to env var RIMGYM_RESET_SAVE)",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help="Socket read timeout per request",
    )
    parser.add_argument(
        "--max-wait-s",
        type=float,
        default=DEFAULT_MAX_WAIT_S,
        help="Max seconds to wait for reset completion",
    )
    parser.add_argument(
        "--poll-interval-s",
        type=float,
        default=DEFAULT_POLL_INTERVAL_S,
        help="Seconds between QUERY_STATE polls",
    )

    args = parser.parse_args()

    rimgym_pb2: Any = _load_protos()

    reset_cmd = rimgym_pb2.CommandMessage()
    reset_cmd.type = rimgym_pb2.CommandType.RESET
    if args.save_name:
        reset_cmd.reset_save_name = args.save_name

    query_cmd = rimgym_pb2.CommandMessage()
    query_cmd.type = rimgym_pb2.CommandType.QUERY_STATE

    started = time.monotonic()

    def elapsed_s() -> float:
        return time.monotonic() - started

    try:
        with socket.create_connection(
            (args.host, args.port), timeout=args.timeout_s
        ) as sock:
            sock.settimeout(args.timeout_s)

            print(
                f"Connecting to {args.host}:{args.port}...\n"
                f"Sending RESET (save_name={args.save_name!r})"
            )

            _send_length_prefixed(sock, reset_cmd.SerializeToString())
            reset_resp_bytes = _recv_length_prefixed(sock)

            # Best-effort parse; treat any parseable response as confirmation.
            rich = rimgym_pb2.RichStateMessage()
            rich.ParseFromString(reset_resp_bytes)

            print(
                f"RESET response: is_ready={getattr(rich, 'is_ready', False)}, "
                f"reset_in_progress={getattr(rich, 'reset_in_progress', False)}, "
                f"status={getattr(rich, 'status_message', '')!r}"
            )

            deadline = started + args.max_wait_s
            last_status = ""
            is_ready = False
            reset_in_progress = False
            status_message = ""

            while time.monotonic() < deadline:
                _send_length_prefixed(sock, query_cmd.SerializeToString())
                resp_bytes = _recv_length_prefixed(sock)

                state = rimgym_pb2.RichStateMessage()
                state.ParseFromString(resp_bytes)

                is_ready = bool(getattr(state, "is_ready", False))
                reset_in_progress = bool(getattr(state, "reset_in_progress", False))
                status_message = str(getattr(state, "status_message", ""))

                if status_message and status_message != last_status:
                    print(f"[{elapsed_s():.1f}s] status={status_message!r}")
                    last_status = status_message

                if (not reset_in_progress) and is_ready:
                    print(
                        f"[{elapsed_s():.1f}s] reset complete: "
                        f"is_ready={is_ready}, reset_in_progress={reset_in_progress}"
                    )
                    return 0

                time.sleep(args.poll_interval_s)

            print(
                f"Timed out after {args.max_wait_s:.1f}s waiting for reset completion. "
                f"Last observed: is_ready={is_ready}, reset_in_progress={reset_in_progress}, "
                f"status={status_message!r}"
            )
            return 1

    except Exception as e:
        print(f"Reset smoke test failed: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
