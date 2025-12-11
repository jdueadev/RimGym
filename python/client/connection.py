"""
Connection Manager for RimWorld ML Bridge.

Handles TCP connection with reconnection logic, health monitoring, and command execution.
"""

import logging
import os
import socket
import struct
import sys
import time
from threading import Lock
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from mlbridge_pb2 import CommandMessage, RichStateMessage, StateMessage

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Raised when connection fails."""

    pass


class ConnectionManager:
    """
    Manages TCP connection to RimWorld server with reconnection logic.

    Features:
    - Length-prefixed protobuf message framing
    - Exponential backoff reconnection
    - Thread-safe command execution
    - Connection health monitoring
    - TASK-014/015: Auto-reconnect on socket errors
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        connect_timeout: float = 10.0,
        reconnect_attempts: int = 10,
        reconnect_backoff: float = 1.0,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 3,
        reconnect_backoff_ms: int = 1000,
    ):
        """
        Initialize connection manager.

        Args:
            host: Server hostname
            port: Server port
            connect_timeout: Connection timeout in seconds
            reconnect_attempts: Max reconnection attempts for initial connect (0 = infinite)
            reconnect_backoff: Initial backoff delay in seconds for initial connect
            auto_reconnect: TASK-014 - Enable automatic reconnection on send errors
            max_reconnect_attempts: TASK-014 - Max reconnect attempts for auto-reconnect
            reconnect_backoff_ms: TASK-014 - Backoff in milliseconds for auto-reconnect
        """
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_backoff = reconnect_backoff

        # TASK-014: Auto-reconnect configuration
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_backoff_ms = reconnect_backoff_ms

        self._socket: Optional[socket.socket] = None
        self._lock = Lock()
        self._connected = False
        self._last_health_check = 0.0

        # Connection state tracking for events
        self._total_reconnects = 0
        self._last_disconnect_time: Optional[float] = None

        logger.info(
            f"ConnectionManager initialized: {host}:{port}, auto_reconnect={auto_reconnect}"
        )

    def connect(self) -> bool:
        """
        Establish connection to RimWorld server.

        Returns:
            True if connected successfully, False otherwise
        """
        with self._lock:
            if self._connected:
                logger.warning("Already connected")
                return True

            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(self.connect_timeout)
                self._socket.connect((self.host, self.port))

                self._connected = True
                self._last_health_check = time.time()

                logger.info(f"Connected to {self.host}:{self.port}")
                return True

            except (socket.error, socket.timeout) as e:
                logger.error(f"Connection failed: {e}")
                if self._socket:
                    try:
                        self._socket.close()
                    except:
                        pass
                    self._socket = None
                self._connected = False
                return False

    def disconnect(self) -> None:
        """Close connection gracefully."""
        with self._lock:
            if self._socket:
                try:
                    self._socket.close()
                    logger.info("Disconnected")
                except Exception as e:
                    logger.warning(f"Error during disconnect: {e}")
                finally:
                    self._socket = None
                    self._connected = False

    def reconnect(self) -> bool:
        """
        Attempt reconnection with exponential backoff.

        Returns:
            True if reconnected successfully, False otherwise
        """
        logger.info("Attempting reconnection...")

        self.disconnect()

        attempt = 0
        backoff = self.reconnect_backoff

        while self.reconnect_attempts == 0 or attempt < self.reconnect_attempts:
            attempt += 1
            logger.info(
                f"Reconnection attempt {attempt}/{self.reconnect_attempts if self.reconnect_attempts > 0 else 'unlimited'}"
            )

            if self.connect():
                logger.info(f"Reconnected after {attempt} attempts")
                return True

            # Exponential backoff with jitter
            time.sleep(backoff + (backoff * 0.1 * (hash(time.time()) % 10)))
            backoff = min(backoff * 2, 30.0)  # Cap at 30s

        logger.error(f"Failed to reconnect after {attempt} attempts")
        return False

    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._connected

    def is_healthy(self) -> bool:
        """
        Check connection health.

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self._connected:
            return False

        # Simple health check: connection exists and no errors
        with self._lock:
            try:
                # Try to peek at socket status
                if self._socket:
                    # Socket exists, assume healthy if connected
                    return True
                return False
            except:
                return False

    def send_command(
        self, command: CommandMessage, timeout: float = 5.0
    ) -> Optional[RichStateMessage]:
        """
        Send command and receive response with length-prefixed framing.
        TASK-015: Implements automatic reconnection on socket errors.

        Args:
            command: Command message to send
            timeout: Response timeout in seconds

        Returns:
            RichStateMessage response (Phase V) or None on error

        Raises:
            ConnectionError: If not connected and reconnection fails
        """
        last_error = None
        attempts = 0
        max_attempts = self.max_reconnect_attempts if self.auto_reconnect else 1

        while attempts < max_attempts:
            attempts += 1

            # Check connection and attempt reconnect if needed
            if not self._connected:
                if self.auto_reconnect and attempts > 1:
                    backoff_seconds = (self.reconnect_backoff_ms / 1000.0) * (
                        2 ** (attempts - 2)
                    )
                    backoff_seconds = min(backoff_seconds, 10.0)  # Cap at 10s
                    logger.info(
                        f"Auto-reconnect attempt {attempts}/{max_attempts} after {backoff_seconds:.1f}s"
                    )
                    time.sleep(backoff_seconds)

                    if self.connect():
                        self._total_reconnects += 1
                        logger.info(
                            f"Auto-reconnect successful (total: {self._total_reconnects})"
                        )
                    else:
                        continue
                elif not self._connected:
                    raise ConnectionError("Not connected")

            try:
                return self._send_command_internal(command, timeout)

            except ConnectionError as e:
                last_error = e
                self._last_disconnect_time = time.time()
                logger.warning(f"Send failed (attempt {attempts}/{max_attempts}): {e}")

                if not self.auto_reconnect:
                    raise

                # Mark as disconnected for next iteration
                self._connected = False

        raise last_error or ConnectionError("Failed after all reconnection attempts")

    def _send_command_internal(
        self, command: CommandMessage, timeout: float
    ) -> RichStateMessage:
        """
        Internal send implementation without reconnection logic.
        """
        with self._lock:
            try:
                # Serialize command
                command_bytes = command.SerializeToString()
                command_length = len(command_bytes)

                # Send length prefix (4 bytes, big-endian)
                length_prefix = struct.pack(">I", command_length)
                self._socket.sendall(length_prefix + command_bytes)

                logger.debug(
                    f"Sent command: {command.command_type} ({command_length} bytes)"
                )

                # Receive response length prefix
                old_timeout = self._socket.gettimeout()
                self._socket.settimeout(timeout)

                try:
                    length_data = self._recv_exact(4)
                    if not length_data:
                        raise ConnectionError("Connection closed by server")

                    response_length = struct.unpack(">I", length_data)[0]

                    # Receive response data
                    response_data = self._recv_exact(response_length)
                    if not response_data:
                        raise ConnectionError("Connection closed by server")

                    # Deserialize response (try RichStateMessage first, fallback to StateMessage)
                    try:
                        response = RichStateMessage()
                        response.ParseFromString(response_data)
                        logger.debug(
                            f"Received RichStateMessage ({response_length} bytes)"
                        )
                    except Exception:
                        # Fallback to legacy StateMessage for backward compatibility
                        logger.debug("Falling back to legacy StateMessage")
                        response = StateMessage()
                        response.ParseFromString(response_data)

                    self._last_health_check = time.time()
                    return response

                finally:
                    self._socket.settimeout(old_timeout)

            except socket.timeout:
                logger.error(f"Command timeout after {timeout}s")
                self._connected = False
                raise ConnectionError(f"Timeout after {timeout}s")

            except (socket.error, struct.error) as e:
                logger.error(f"Send command failed: {e}")
                self._connected = False
                raise ConnectionError(f"Send failed: {e}")

    def _recv_exact(self, n: int) -> bytes:
        """
        Receive exactly n bytes from socket.

        Args:
            n: Number of bytes to receive

        Returns:
            Received bytes

        Raises:
            ConnectionError: If connection closed before receiving all bytes
        """
        data = b""
        while len(data) < n:
            chunk = self._socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data")
            data += chunk
        return data

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
