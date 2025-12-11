"""
Unit tests for queue implementations.
"""

import threading
import time

import pytest

from client.queues import ActionQueue, EventPriority, EventQueue, StateQueue


@pytest.mark.unit
class TestStateQueue:
    """Test StateQueue functionality."""

    def test_init(self):
        """Test initialization."""
        q = StateQueue(maxsize=5)
        assert q.empty()
        assert q.qsize() == 0
        assert q.dropped_count == 0

    def test_put_get(self):
        """Test basic put and get operations."""
        q = StateQueue()
        state = {"frame": 1, "data": "test"}

        result = q.put(state)
        assert result is True
        assert q.qsize() == 1

        retrieved = q.get(timeout=0.1)
        assert retrieved == state
        assert q.empty()

    def test_overflow_drops_oldest(self):
        """Test that overflow drops oldest state."""
        q = StateQueue(maxsize=3)

        # Fill queue
        q.put({"frame": 1})
        q.put({"frame": 2})
        q.put({"frame": 3})

        # Add one more - should drop frame 1
        q.put({"frame": 4})

        assert q.qsize() == 3
        assert q.dropped_count == 1

        # Should get frames 2, 3, 4
        assert q.get()["frame"] == 2
        assert q.get()["frame"] == 3
        assert q.get()["frame"] == 4

    def test_get_latest(self):
        """Test get_latest skips to newest state."""
        q = StateQueue()

        q.put({"frame": 1})
        q.put({"frame": 2})
        q.put({"frame": 3})

        latest = q.get_latest()
        assert latest["frame"] == 3
        assert q.empty()

    def test_get_latest_empty(self):
        """Test get_latest on empty queue."""
        q = StateQueue()
        latest = q.get_latest()
        assert latest is None

    def test_timeout(self):
        """Test get timeout."""
        q = StateQueue()

        # get() returns None on timeout (doesn't raise Empty)
        result = q.get(timeout=0.1)
        assert result is None

    def test_thread_safety(self):
        """Test thread-safe operations."""
        q = StateQueue(maxsize=100)
        errors = []

        def producer():
            try:
                for i in range(100):
                    q.put({"frame": i})
            except Exception as e:
                errors.append(e)

        def consumer():
            try:
                for _ in range(100):
                    q.get(timeout=1.0)
            except Exception as e:
                errors.append(e)

        prod_thread = threading.Thread(target=producer)
        cons_thread = threading.Thread(target=consumer)

        prod_thread.start()
        cons_thread.start()

        prod_thread.join()
        cons_thread.join()

        assert len(errors) == 0
        assert q.empty()


@pytest.mark.unit
class TestEventQueue:
    """Test EventQueue functionality."""

    def test_init(self):
        """Test initialization."""
        q = EventQueue(maxsize=10)
        assert q.empty()
        assert q.qsize() == 0
        assert q.dropped_count == 0

    def test_put_get_priority(self):
        """Test priority ordering."""
        q = EventQueue()

        # Add events with different priorities
        q.put("low", EventPriority.LOW)
        q.put("high", EventPriority.HIGH)
        q.put("critical", EventPriority.CRITICAL)
        q.put("medium", EventPriority.MEDIUM)

        # Should get in priority order
        assert q.get(timeout=0.1) == "critical"
        assert q.get(timeout=0.1) == "high"
        assert q.get(timeout=0.1) == "medium"
        assert q.get(timeout=0.1) == "low"

    def test_overflow_drops(self):
        """Test that overflow drops events."""
        q = EventQueue(maxsize=3)

        # Fill queue
        q.put("event1", EventPriority.LOW)
        q.put("event2", EventPriority.LOW)
        q.put("event3", EventPriority.LOW)

        # Try to add more
        result = q.put("event4", EventPriority.LOW)

        assert result is False
        assert q.dropped_count == 1
        assert q.qsize() == 3

    def test_priority_enum(self):
        """Test EventPriority enum values."""
        assert EventPriority.CRITICAL.value == 0
        assert EventPriority.HIGH.value == 1
        assert EventPriority.MEDIUM.value == 2
        assert EventPriority.LOW.value == 3

        # Lower value = higher priority (compare by value)
        assert EventPriority.CRITICAL.value < EventPriority.HIGH.value
        assert EventPriority.HIGH.value < EventPriority.MEDIUM.value


@pytest.mark.unit
class TestActionQueue:
    """Test ActionQueue functionality."""

    def test_init(self):
        """Test initialization."""
        q = ActionQueue(maxsize=10)
        assert q.empty()
        assert q.qsize() == 0
        assert q.dropped_count == 0

    def test_put_get(self):
        """Test basic FIFO operations."""
        q = ActionQueue()

        q.put("action1")
        q.put("action2")
        q.put("action3")

        assert q.get(timeout=0.1) == "action1"
        assert q.get(timeout=0.1) == "action2"
        assert q.get(timeout=0.1) == "action3"

    def test_overflow_drops(self):
        """Test that overflow drops actions."""
        q = ActionQueue(maxsize=2)

        q.put("action1")
        q.put("action2")
        result = q.put("action3")

        assert result is False
        assert q.dropped_count == 1
        assert q.qsize() == 2

    def test_timeout(self):
        """Test get timeout."""
        q = ActionQueue()

        # get() returns None on timeout (doesn't raise Empty)
        result = q.get(timeout=0.1)
        assert result is None


@pytest.mark.unit
class TestQueuesIntegration:
    """Integration tests for queue interactions."""

    def test_realistic_producer_consumer(self):
        """Test realistic multi-threaded scenario."""
        state_q = StateQueue(maxsize=10)
        EventQueue(maxsize=100)
        ActionQueue(maxsize=100)

        stop_event = threading.Event()
        states_produced = []
        states_consumed = []

        def state_producer():
            """Simulate Listener thread."""
            for i in range(50):
                if stop_event.is_set():
                    break
                state = {"frame": i}
                state_q.put(state)
                states_produced.append(i)
                time.sleep(0.01)

        def state_consumer():
            """Simulate Inference thread."""
            while not stop_event.is_set():
                state = state_q.get(timeout=0.5)
                if state is None:  # Timeout, not Empty exception
                    continue
                states_consumed.append(state["frame"])

        producer = threading.Thread(target=state_producer)
        consumer = threading.Thread(target=state_consumer)

        producer.start()
        time.sleep(0.05)  # Let producer get ahead
        consumer.start()

        producer.join()
        stop_event.set()
        consumer.join()

        # Consumer should have gotten most states
        # (Some might be dropped due to overflow)
        assert len(states_consumed) > 0
        assert len(states_consumed) <= len(states_produced)
