#!/usr/bin/env python3
"""One-shot connectivity check for RimTCP targets.

For now, this script is intentionally minimal: it attempts a single TCP
connection to the first target in `RIMTCP_TARGETS` (format:
`host:port,host:port,...`). If the connection succeeds, it prints a success
message and exits 0. If it fails, it prints an error and exits non-zero.

Example:
    RIMTCP_TARGETS=rimworld_1:50051,rimworld_2:50051 \
        uv run --project /app/src/RimGym python -u /app/src/RimGym/src/examples/vector_worker.py
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import socket
import sys
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Target:
    host: str
    port: int

    @property
    def key(self) -> str:
        return f"{self.host}:{self.port}"


def _parse_targets(raw: str) -> List[Target]:
    raw = raw.strip()
    if not raw:
        raise ValueError("RIMTCP_TARGETS is empty")

    targets: List[Target] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue

        if ":" not in part:
            raise ValueError(
                f"Invalid target '{part}'. Expected host:port (e.g. rimworld_1:50051)"
            )

        host, port_s = part.rsplit(":", 1)
        host = host.strip()
        port_s = port_s.strip()
        if not host:
            raise ValueError(f"Invalid target '{part}': empty host")
        try:
            port = int(port_s)
        except ValueError as exc:
            raise ValueError(f"Invalid target '{part}': port is not an int") from exc

        targets.append(Target(host=host, port=port))

    if not targets:
        raise ValueError("No valid targets parsed from RIMTCP_TARGETS")

    # De-duplicate while preserving order.
    seen = set()
    unique: List[Target] = []
    for t in targets:
        if t.key in seen:
            continue
        seen.add(t.key)
        unique.append(t)

    return unique


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="One-shot RimTCP connectivity check")
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=float(os.environ.get("RIMTCP_CONNECT_TIMEOUT_S", "5")),
        help="TCP connect timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("RIMTCP_WORKER_LOG_LEVEL", "INFO"),
        help="Log level (default: INFO)",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("vector_worker")

    raw_targets = os.environ.get("RIMTCP_TARGETS", "").strip()
    if not raw_targets:
        logger.error(
            "RIMTCP_TARGETS is not set. Example: rimworld_1:50051,rimworld_2:50051"
        )
        return 2

    try:
        targets = _parse_targets(raw_targets)
    except ValueError as e:
        logger.error(str(e))
        return 2

    primary = targets[0]
    logger.info("Connectivity check")
    logger.info("Primary target: %s", primary.key)

    stop = False

    def _request_stop(signum: int, _frame) -> None:
        nonlocal stop
        logger.info("Received signal %s; stopping...", signum)
        stop = True

    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    try:
        if stop:
            logger.info("Stopping before connect attempt")
            return 0

        with socket.create_connection(
            (primary.host, primary.port), timeout=float(args.timeout_s)
        ):
            pass

        logger.info("Successfully connected to %s", primary.key)
        return 0

    except Exception as e:
        logger.exception("Worker failed: %s", e)
        return 1

    finally:
        # No cleanup required beyond the socket context manager.
        pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
