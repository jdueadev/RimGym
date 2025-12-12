#!/usr/bin/env python3
"""RimTCP healthcheck probe.

Purpose:
- Verify the server is not only listening on TCP, but also speaking the expected
  length-prefixed Protobuf protocol and returning a parseable response.

This is intended for Docker Compose `healthcheck` usage:
- fast (single request/response)
- deterministic (no retries/loops inside)
- returns exit code 0 on success, 1 on failure
"""

from __future__ import annotations

import socket
import struct
import sys
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 50051
CONNECT_TIMEOUT_S = 1.0
READ_TIMEOUT_S = 1.0
MAX_RESPONSE_BYTES = 8 * 1024 * 1024  # 8 MiB


def _local_proto_paths() -> list[str]:
    """Return paths that may contain generated protos in container images.

    Supports both:
    - repo/dev layout: /app/src/shared/python/src/rimgym_pb2.py
    - lean runtime image layout: <probe_dir>/../protos/rimgym_pb2.py
    """

    here = Path(__file__).resolve()
    return [
        str(here.parent),
        str(here.parent.parent / "protos"),
    ]


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


def main() -> int:
    try:
        from shared.python.src import rimgym_pb2  # type: ignore
    except Exception:
        for p in _local_proto_paths():
            if p not in sys.path:
                sys.path.insert(0, p)
        try:
            import rimgym_pb2  # type: ignore
        except Exception:
            return 1

    command = rimgym_pb2.CommandMessage()
    command.type = rimgym_pb2.CommandType.QUERY_STATE

    try:
        with socket.create_connection(
            (DEFAULT_HOST, DEFAULT_PORT), timeout=CONNECT_TIMEOUT_S
        ) as sock:
            sock.settimeout(READ_TIMEOUT_S)

            _send_length_prefixed(sock, command.SerializeToString())
            response_bytes = _recv_length_prefixed(sock)

        # Validate response is parseable. We accept either RichStateMessage or StateMessage.
        # (Depending on server mode/version, the response might not include Phase V fields.)
        rich = rimgym_pb2.RichStateMessage()
        rich.ParseFromString(response_bytes)

        # Avoid false positives on empty/garbage responses: require the server to at least
        # populate one of these common fields.
        if rich.frame_id != 0 or rich.is_ready or rich.status_message:
            return 0

        state = rimgym_pb2.StateMessage()
        state.ParseFromString(response_bytes)
        if state.frame_id != 0 or state.is_ready or state.status_message:
            return 0

        return 1
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
