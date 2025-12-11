"""
Unit tests for ConnectionManager.
"""

import socket
import threading
from unittest.mock import MagicMock, patch

import pytest
from client.connection import ConnectionManager


class TestConnectionManager:
    """Test ConnectionManager functionality."""

    def test_init(self):
        """Test initialization."""
        conn = ConnectionManager(
            host="localhost",
            port=50051,
            connect_timeout=5.0,
            reconnect_attempts=5,
            reconnect_backoff=0.5,
        )

        assert conn.host == "localhost"
        assert conn.port == 50051
        assert conn._connect_timeout == 5.0
        assert conn._reconnect_attempts == 5
        assert conn._reconnect_backoff == 0.5
        assert not conn.is_connected()

    @patch("socket.socket")
    def test_connect_success(self, mock_socket_class):
        """Test successful connection."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        conn = ConnectionManager()
        result = conn.connect()

        assert result is True
        assert conn.is_connected()
        mock_sock.connect.assert_called_once_with(("localhost", 50051))
        mock_sock.settimeout.assert_called()

    @patch("socket.socket")
    def test_connect_failure(self, mock_socket_class):
        """Test connection failure."""
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = socket.error("Connection refused")
        mock_socket_class.return_value = mock_sock

        conn = ConnectionManager()
        result = conn.connect()

        assert result is False
        assert not conn.is_connected()

    @patch("socket.socket")
    def test_disconnect(self, mock_socket_class):
        """Test disconnection."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        conn = ConnectionManager()
        conn.connect()
        conn.disconnect()

        assert not conn.is_connected()
        mock_sock.close.assert_called_once()

    @patch("socket.socket")
    @patch("time.sleep")
    def test_reconnect_with_backoff(self, mock_sleep, mock_socket_class):
        """Test reconnection with exponential backoff."""
        mock_sock = MagicMock()

        # First attempt fails, second succeeds
        mock_sock.connect.side_effect = [
            socket.error("Connection refused"),
            None,  # Success
        ]
        mock_socket_class.return_value = mock_sock

        conn = ConnectionManager(reconnect_attempts=3, reconnect_backoff=1.0)
        result = conn.reconnect()

        assert result is True
        assert conn.is_connected()

        # Should have slept once (after first failure)
        assert mock_sleep.call_count == 1
        # First backoff should be 1.0s
        mock_sleep.assert_called_with(1.0)

    @patch("socket.socket")
    @patch("time.sleep")
    def test_reconnect_max_attempts(self, mock_sleep, mock_socket_class):
        """Test reconnection respects max attempts."""
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = socket.error("Connection refused")
        mock_socket_class.return_value = mock_sock

        conn = ConnectionManager(reconnect_attempts=3, reconnect_backoff=0.5)
        result = conn.reconnect()

        assert result is False
        assert not conn.is_connected()

        # Should try 3 times: 3 connect attempts, 3 sleeps
        assert mock_sock.connect.call_count == 3
        assert mock_sleep.call_count == 3

    @patch("socket.socket")
    @patch("time.sleep")
    def test_exponential_backoff_calculation(self, mock_sleep, mock_socket_class):
        """Test exponential backoff multiplier and cap."""
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = socket.error("Connection refused")
        mock_socket_class.return_value = mock_sock

        conn = ConnectionManager(reconnect_attempts=5, reconnect_backoff=1.0)
        conn.reconnect()

        # Should sleep with: 1s, 2s, 4s, 8s, 16s
        # But capped at 30s, so: 1s, 2s, 4s, 8s, 16s
        expected_sleeps = [1.0, 2.0, 4.0, 8.0, 16.0]
        actual_sleeps = [call[0][0] for call in mock_sleep.call_args_list]

        assert actual_sleeps == expected_sleeps

    def test_is_healthy(self):
        """Test health check."""
        conn = ConnectionManager()

        # Not connected - not healthy
        assert not conn.is_healthy()

    @patch("socket.socket")
    def test_context_manager(self, mock_socket_class):
        """Test context manager usage."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        with ConnectionManager() as conn:
            assert conn.is_connected()

        # Should disconnect on exit
        assert not conn.is_connected()
        mock_sock.close.assert_called()

    @patch("socket.socket")
    def test_thread_safety(self, mock_socket_class):
        """Test thread-safe operations."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        conn = ConnectionManager()
        conn.connect()

        errors = []

        def worker():
            try:
                for _ in range(100):
                    conn.is_connected()
                    conn.is_healthy()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestConnectionManagerIntegration:
    """Integration tests requiring actual network (optional)."""

    @pytest.mark.skipif(True, reason="Requires RimWorld server running")
    def test_real_connection(self):
        """Test actual connection to RimWorld server."""
        conn = ConnectionManager(host="localhost", port=50051)
        result = conn.connect()

        assert result is True
        assert conn.is_connected()

        conn.disconnect()
        assert not conn.is_connected()
