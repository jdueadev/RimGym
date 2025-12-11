"""
Unit tests for ListenerThread.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from queue import Empty

from client.listener import ListenerThread, EventDetectionConfig
from client.queues import StateQueue, EventQueue, EventPriority, ActionQueue
from mlbridge_pb2 import CommandMessage, StateMessage


class TestEventDetectionConfig:
    """Test EventDetectionConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = EventDetectionConfig()
        
        assert config.health_critical_threshold == 0.2
        assert config.health_warning_threshold == 0.5
        assert config.movement_threshold == 0.5
        assert config.detect_job_changes is True
        assert config.detect_new_colonists is True
        assert config.detect_dead_colonists is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = EventDetectionConfig(
            health_critical_threshold=0.1,
            health_warning_threshold=0.3,
            detect_job_changes=False
        )
        
        assert config.health_critical_threshold == 0.1
        assert config.health_warning_threshold == 0.3
        assert config.detect_job_changes is False


class TestListenerThread:
    """Test ListenerThread functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.connection = Mock()
        self.state_queue = StateQueue(maxsize=10)
        self.event_queue = EventQueue(maxsize=100)
        self.stop_event = threading.Event()
        self.metrics = Mock()
        
        self.listener = ListenerThread(
            connection_manager=self.connection,
            state_queue=self.state_queue,
            event_queue=self.event_queue,
            stop_event=self.stop_event,
            poll_interval_ms=100,
            metrics_collector=self.metrics
        )
    
    def teardown_method(self):
        """Clean up after tests."""
        self.stop_event.set()
        if self.listener.is_alive():
            self.listener.join(timeout=1.0)
    
    def test_initialization(self):
        """Test thread initialization."""
        assert self.listener.connection == self.connection
        assert self.listener.state_queue == self.state_queue
        assert self.listener.event_queue == self.event_queue
        assert self.listener.poll_interval == 0.1
        assert self.listener._poll_count == 0
        assert self.listener._event_count == 0
    
    def test_parse_state_message(self):
        """Test state message parsing."""
        # Create mock state message
        msg = StateMessage()
        msg.frame_id = 100
        
        state = self.listener._parse_state_message(msg)
        
        assert state["frame_id"] == 100
        assert "timestamp" in state  # Added by parser
        assert "colonists" in state
        assert "game_state" in state
    
    def test_initialize_tracking(self):
        """Test tracking initialization."""
        state = {
            "colonists": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        
        self.listener._initialize_tracking(state)
        
        assert len(self.listener._known_colonist_ids) == 2
        assert 1 in self.listener._known_colonist_ids
        assert 2 in self.listener._known_colonist_ids
    
    def test_detect_new_colonist(self):
        """Test new colonist detection."""
        # Set up previous state
        previous = [
            {"id": 1, "name": "Alice", "health": 1.0}
        ]
        
        # New state with additional colonist
        current = [
            {"id": 1, "name": "Alice", "health": 1.0},
            {"id": 2, "name": "Bob", "health": 1.0}
        ]
        
        self.listener._known_colonist_ids = {1}
        events = self.listener._detect_colonist_events(current, previous)
        
        # Should detect new colonist
        assert len(events) == 1
        priority, event_data = events[0]
        assert priority == EventPriority.MEDIUM
        assert event_data["type"] == "colonist_joined"
        assert event_data["colonist_id"] == 2
        assert event_data["name"] == "Bob"
    
    def test_detect_missing_colonist(self):
        """Test missing/dead colonist detection."""
        # Set up previous state
        previous = [
            {"id": 1, "name": "Alice", "health": 1.0},
            {"id": 2, "name": "Bob", "health": 0.3}
        ]
        
        # New state with colonist removed
        current = [
            {"id": 1, "name": "Alice", "health": 1.0}
        ]
        
        self.listener._known_colonist_ids = {1, 2}
        events = self.listener._detect_colonist_events(current, previous)
        
        # Should detect missing colonist
        assert len(events) == 1
        priority, event_data = events[0]
        assert priority == EventPriority.HIGH
        assert event_data["type"] == "colonist_missing"
        assert event_data["colonist_id"] == 2
        assert event_data["last_health"] == 0.3
    
    def test_detect_critical_health(self):
        """Test critical health event detection."""
        # Set up previous state
        previous = [
            {"id": 1, "name": "Alice", "health": 0.5}
        ]
        
        # New state with health drop
        current = [
            {"id": 1, "name": "Alice", "health": 0.15}
        ]
        
        self.listener._known_colonist_ids = {1}
        events = self.listener._detect_colonist_events(current, previous)
        
        # Should detect critical health
        assert len(events) == 1
        priority, event_data = events[0]
        assert priority == EventPriority.CRITICAL
        assert event_data["type"] == "health_critical"
        assert event_data["colonist_id"] == 1
        assert event_data["health"] == 0.15
    
    def test_detect_health_warning(self):
        """Test health warning event detection."""
        # Set up previous state
        previous = [
            {"id": 1, "name": "Alice", "health": 0.8}
        ]
        
        # New state with health drop
        current = [
            {"id": 1, "name": "Alice", "health": 0.4}
        ]
        
        self.listener._known_colonist_ids = {1}
        events = self.listener._detect_colonist_events(current, previous)
        
        # Should detect health warning
        assert len(events) == 1
        priority, event_data = events[0]
        assert priority == EventPriority.HIGH
        assert event_data["type"] == "health_warning"
        assert event_data["health"] == 0.4
    
    def test_detect_job_change(self):
        """Test job change detection."""
        # Set up previous state
        previous = [
            {"id": 1, "name": "Alice", "health": 1.0, "current_job": "Mining"}
        ]
        
        # New state with job change
        current = [
            {"id": 1, "name": "Alice", "health": 1.0, "current_job": "Hauling"}
        ]
        
        self.listener._known_colonist_ids = {1}
        events = self.listener._detect_colonist_events(current, previous)
        
        # Should detect job change
        assert len(events) == 1
        priority, event_data = events[0]
        assert priority == EventPriority.LOW
        assert event_data["type"] == "job_changed"
        assert event_data["old_job"] == "Mining"
        assert event_data["new_job"] == "Hauling"
    
    def test_no_events_on_first_state(self):
        """Test that no events are generated on first state."""
        state = {
            "colonists": [
                {"id": 1, "name": "Alice", "health": 1.0}
            ]
        }
        
        events = self.listener._detect_events(state)
        
        # First state should not generate events
        assert len(events) == 0
        # But should initialize tracking
        assert 1 in self.listener._known_colonist_ids
    
    def test_multiple_events(self):
        """Test detecting multiple events at once."""
        # Set up previous state
        previous = [
            {"id": 1, "name": "Alice", "health": 0.8, "current_job": "Mining"},
            {"id": 2, "name": "Bob", "health": 1.0, "current_job": "Hauling"}
        ]
        
        # New state with multiple changes
        current = [
            {"id": 1, "name": "Alice", "health": 0.15, "current_job": "Mining"},
            {"id": 2, "name": "Bob", "health": 1.0, "current_job": "Construction"},
            {"id": 3, "name": "Charlie", "health": 1.0, "current_job": "Growing"}
        ]
        
        self.listener._known_colonist_ids = {1, 2}
        events = self.listener._detect_colonist_events(current, previous)
        
        # Should detect: critical health + job change + new colonist
        assert len(events) == 3
        
        event_types = {e[1]["type"] for e in events}
        assert "health_critical" in event_types
        assert "job_changed" in event_types
        assert "colonist_joined" in event_types
    
    def test_disabled_event_detection(self):
        """Test that disabled event types are not detected."""
        config = EventDetectionConfig(
            detect_job_changes=False,
            detect_new_colonists=False
        )
        
        listener = ListenerThread(
            connection_manager=self.connection,
            state_queue=self.state_queue,
            event_queue=self.event_queue,
            stop_event=self.stop_event,
            event_config=config
        )
        
        # Previous and current with job change and new colonist
        previous = [
            {"id": 1, "name": "Alice", "health": 1.0, "current_job": "Mining"}
        ]
        
        current = [
            {"id": 1, "name": "Alice", "health": 1.0, "current_job": "Hauling"},
            {"id": 2, "name": "Bob", "health": 1.0, "current_job": "Growing"}
        ]
        
        listener._known_colonist_ids = {1}
        events = listener._detect_colonist_events(current, previous)
        
        # Should not detect job change or new colonist
        assert len(events) == 0
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        self.listener._poll_count = 100
        self.listener._event_count = 25
        self.listener._known_colonist_ids = {1, 2, 3}
        
        stats = self.listener.get_stats()
        
        assert stats["poll_count"] == 100
        assert stats["event_count"] == 25
        assert stats["known_colonists"] == 3


class TestListenerThreadIntegration:
    """Integration tests for Listener thread."""
    
    def test_thread_lifecycle(self):
        """Test starting and stopping the thread."""
        connection = Mock()
        connection.send_command = Mock(return_value=None)
        connection.is_healthy = Mock(return_value=True)
        
        state_queue = StateQueue(maxsize=10)
        event_queue = EventQueue(maxsize=100)
        stop_event = threading.Event()
        
        listener = ListenerThread(
            connection_manager=connection,
            state_queue=state_queue,
            event_queue=event_queue,
            stop_event=stop_event,
            poll_interval_ms=50
        )
        
        # Start thread
        listener.start()
        assert listener.is_alive()
        
        # Let it run for a bit
        time.sleep(0.2)
        
        # Stop thread
        stop_event.set()
        listener.join(timeout=1.0)
        
        assert not listener.is_alive()
    
    def test_state_polling_and_queuing(self):
        """Test that states are polled and queued."""
        # Mock connection that returns states
        connection = Mock()
        connection.is_healthy = Mock(return_value=True)
        connection.is_connected = Mock(return_value=True)
        
        call_count = [0]
        def mock_send_command(cmd, timeout=None):
            call_count[0] += 1
            msg = StateMessage()
            msg.frame_id = 100 + call_count[0]
            return msg
        
        connection.send_command = mock_send_command
        
        state_queue = StateQueue(maxsize=10)
        event_queue = EventQueue(maxsize=100)
        stop_event = threading.Event()
        
        listener = ListenerThread(
            connection_manager=connection,
            state_queue=state_queue,
            event_queue=event_queue,
            stop_event=stop_event,
            poll_interval_ms=50
        )
        
        listener.start()
        
        # Wait for some polls
        time.sleep(0.4)
        
        # Stop thread
        stop_event.set()
        listener.join(timeout=1.0)
        
        # Should have queued some states
        assert state_queue.qsize() > 0, f"Expected states in queue, got {state_queue.qsize()}. Polls: {call_count[0]}"
        
        # Verify state content
        state = state_queue.get()
        assert state["frame_id"] >= 100
    
    @pytest.mark.skipif(True, reason="Requires RimWorld server running")
    def test_real_connection(self):
        """Test with real RimWorld connection."""
        from client.connection import ConnectionManager
        
        connection = ConnectionManager(host="localhost", port=50051)
        connection.connect()
        
        state_queue = StateQueue(maxsize=10)
        event_queue = EventQueue(maxsize=100)
        stop_event = threading.Event()
        
        listener = ListenerThread(
            connection_manager=connection,
            state_queue=state_queue,
            event_queue=event_queue,
            stop_event=stop_event,
            poll_interval_ms=100
        )
        
        listener.start()
        
        # Run for 2 seconds
        time.sleep(2.0)
        
        stop_event.set()
        listener.join(timeout=2.0)
        
        connection.disconnect()
        
        # Should have collected states
        assert state_queue.qsize() > 0
        
        # Check stats
        stats = listener.get_stats()
        assert stats["poll_count"] > 0
