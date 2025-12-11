#!/usr/bin/env python3
"""
RimWorld Server Health Check Diagnostics

TASK-002: Diagnostic script to test connection, send QUERY_STATE, and log response times.
Monitors RimWorld server stability over time and identifies failure patterns.

Usage:
    uv run python python/diagnostics/check_rimworld_health.py [--duration MINUTES] [--interval SECONDS]
"""

import argparse
import json
import logging
import socket
import struct
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.python.src.mlbridge_pb2 import CommandMessage, RichStateMessage

# Minimum success rate threshold for health check to pass
MIN_SUCCESS_RATE_PERCENT = 95.0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    timestamp: datetime
    success: bool
    response_time_ms: float
    frame_id: int = 0
    colonist_count: int = 0
    error_message: str = ""


@dataclass
class HealthCheckStats:
    """Aggregated statistics from health checks."""

    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    total_response_time_ms: float = 0.0
    min_response_time_ms: float = float("inf")
    max_response_time_ms: float = 0.0
    errors: list = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    last_check_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100

    @property
    def avg_response_time_ms(self) -> float:
        """Calculate average response time."""
        if self.successful_checks == 0:
            return 0.0
        return self.total_response_time_ms / self.successful_checks

    def record(self, result: HealthCheckResult):
        """Record a health check result."""
        self.total_checks += 1
        self.last_check_time = result.timestamp

        if result.success:
            self.successful_checks += 1
            self.total_response_time_ms += result.response_time_ms
            self.min_response_time_ms = min(
                self.min_response_time_ms, result.response_time_ms
            )
            self.max_response_time_ms = max(
                self.max_response_time_ms, result.response_time_ms
            )
        else:
            self.failed_checks += 1
            self.errors.append(
                {
                    "timestamp": result.timestamp.isoformat(),
                    "error": result.error_message,
                }
            )

    def to_dict(self) -> dict:
        """Convert stats to dictionary for JSON export."""
        return {
            "total_checks": self.total_checks,
            "successful_checks": self.successful_checks,
            "failed_checks": self.failed_checks,
            "success_rate_percent": round(self.success_rate, 2),
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "min_response_time_ms": round(self.min_response_time_ms, 2)
            if self.min_response_time_ms != float("inf")
            else None,
            "max_response_time_ms": round(self.max_response_time_ms, 2),
            "duration_seconds": (self.last_check_time - self.start_time).total_seconds()
            if self.last_check_time
            else 0,
            "errors": self.errors[-10:],  # Last 10 errors
        }


class RimWorldHealthChecker:
    """Health checker for RimWorld server."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.stats = HealthCheckStats()

    def _send_command(self, sock: socket.socket, command: CommandMessage) -> bytes:
        """Send a length-prefixed protobuf message."""
        data = command.SerializeToString()
        length_prefix = struct.pack(">I", len(data))
        sock.sendall(length_prefix + data)

    def _receive_response(self, sock: socket.socket) -> RichStateMessage:
        """Receive a length-prefixed protobuf message."""
        # Read 4-byte length prefix
        length_data = b""
        while len(length_data) < 4:
            chunk = sock.recv(4 - len(length_data))
            if not chunk:
                raise ConnectionError("Connection closed while reading length prefix")
            length_data += chunk

        length = struct.unpack(">I", length_data)[0]

        # Read message body
        data = b""
        while len(data) < length:
            chunk = sock.recv(min(length - len(data), 4096))
            if not chunk:
                raise ConnectionError("Connection closed while reading message body")
            data += chunk

        response = RichStateMessage()
        response.ParseFromString(data)
        return response

    def check_health(self) -> HealthCheckResult:
        """
        Perform a single health check.

        Returns:
            HealthCheckResult with success status and timing
        """
        timestamp = datetime.now()
        start_time = time.perf_counter()

        try:
            # Create socket and connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connect_timeout)
            sock.connect((self.host, self.port))
            sock.settimeout(self.read_timeout)

            # Send QUERY_STATE command
            command = CommandMessage()
            command.command_type = CommandMessage.QUERY_STATE

            self._send_command(sock, command)
            response = self._receive_response(sock)

            # Calculate response time
            response_time_ms = (time.perf_counter() - start_time) * 1000

            # Extract state info
            colonist_count = len(response.colonists) if response.colonists else 0

            result = HealthCheckResult(
                timestamp=timestamp,
                success=True,
                response_time_ms=response_time_ms,
                frame_id=response.frame_id,
                colonist_count=colonist_count,
            )

            logger.info(
                f"✓ Health check passed: {response_time_ms:.1f}ms, "
                f"frame={response.frame_id}, colonists={colonist_count}"
            )

        except socket.timeout:
            result = HealthCheckResult(
                timestamp=timestamp,
                success=False,
                response_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message="Connection timeout",
            )
            logger.error("✗ Health check failed: Connection timeout")

        except ConnectionRefusedError:
            result = HealthCheckResult(
                timestamp=timestamp,
                success=False,
                response_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message="Connection refused - server not running",
            )
            logger.error("✗ Health check failed: Connection refused")

        except ConnectionError as e:
            result = HealthCheckResult(
                timestamp=timestamp,
                success=False,
                response_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=str(e),
            )
            logger.error(f"✗ Health check failed: {e}")

        except Exception as e:
            result = HealthCheckResult(
                timestamp=timestamp,
                success=False,
                response_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Unexpected error: {e}",
            )
            logger.error(f"✗ Health check failed: {e}")

        finally:
            try:
                sock.close()
            except Exception:
                pass

        self.stats.record(result)
        return result

    def run_continuous(
        self,
        duration_minutes: float = 5.0,
        interval_seconds: float = 1.0,
        output_file: Optional[str] = None,
    ):
        """
        Run continuous health checks for specified duration.

        Args:
            duration_minutes: How long to run checks
            interval_seconds: Time between checks
            output_file: Optional JSON file to write results
        """
        logger.info(
            f"Starting health check monitoring for {duration_minutes} minutes "
            f"(interval: {interval_seconds}s)"
        )
        logger.info(f"Target: {self.host}:{self.port}")
        logger.info("-" * 60)

        end_time = time.time() + (duration_minutes * 60)

        try:
            while time.time() < end_time:
                self.check_health()
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("\nMonitoring interrupted by user")

        # Print summary
        logger.info("-" * 60)
        logger.info("HEALTH CHECK SUMMARY")
        logger.info("-" * 60)
        stats = self.stats.to_dict()
        logger.info(f"Total checks:     {stats['total_checks']}")
        logger.info(f"Successful:       {stats['successful_checks']}")
        logger.info(f"Failed:           {stats['failed_checks']}")
        logger.info(f"Success rate:     {stats['success_rate_percent']}%")
        logger.info(f"Avg response:     {stats['avg_response_time_ms']}ms")
        logger.info(f"Min response:     {stats['min_response_time_ms']}ms")
        logger.info(f"Max response:     {stats['max_response_time_ms']}ms")
        logger.info(f"Duration:         {stats['duration_seconds']:.1f}s")

        if stats["errors"]:
            logger.info(f"\nLast {len(stats['errors'])} errors:")
            for err in stats["errors"]:
                logger.info(f"  {err['timestamp']}: {err['error']}")

        # Write to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(stats, f, indent=2)
            logger.info(f"\nResults written to: {output_file}")

        return stats


def main():
    """Main entry point for health check diagnostics."""
    parser = argparse.ArgumentParser(
        description="RimWorld Server Health Check Diagnostics"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="RimWorld server host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=50051,
        help="RimWorld server port (default: 50051)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Duration in minutes (default: 5)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Interval between checks in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file for results",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Run single health check and exit",
    )

    args = parser.parse_args()

    checker = RimWorldHealthChecker(host=args.host, port=args.port)

    if args.single:
        result = checker.check_health()
        sys.exit(0 if result.success else 1)
    else:
        stats = checker.run_continuous(
            duration_minutes=args.duration,
            interval_seconds=args.interval,
            output_file=args.output,
        )
        # Exit with error if success rate < MIN_SUCCESS_RATE_PERCENT%
        sys.exit(0 if stats["success_rate_percent"] >= MIN_SUCCESS_RATE_PERCENT else 1)


if __name__ == "__main__":
    main()
