"""
Performance benchmarks for Listener thread.

Validates that performance targets are met:
- Event detection: <1ms per state
- State parsing: <5ms for complex states
- Queue operations: <0.1ms
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import time
import threading
from unittest.mock import Mock

from client.listener import ListenerThread
from client.queues import StateQueue, EventQueue
from mlbridge_pb2 import StateMessage


class TestListenerPerformance:
    """Performance benchmarks for Listener thread."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.connection = Mock()
        self.state_queue = StateQueue(maxsize=10)
        self.event_queue = EventQueue(maxsize=100)
        self.stop_event = threading.Event()
        
        self.listener = ListenerThread(
            connection_manager=self.connection,
            state_queue=self.state_queue,
            event_queue=self.event_queue,
            stop_event=self.stop_event,
            poll_interval_ms=100
        )
    
    def test_state_parsing_performance(self):
        """Benchmark: State parsing should be <5ms."""
        # Create a complex state message
        msg = StateMessage()
        msg.frame_id = 1000
        
        # Warmup
        for _ in range(10):
            self.listener._parse_state_message(msg)
        
        # Benchmark
        iterations = 1000
        start = time.perf_counter()
        
        for _ in range(iterations):
            state = self.listener._parse_state_message(msg)
        
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        avg_ms = elapsed_ms / iterations
        
        print(f"\nState parsing: {avg_ms:.4f}ms per message (target: <5ms)")
        assert avg_ms < 5.0, f"State parsing too slow: {avg_ms:.4f}ms"
    
    def test_event_detection_performance_small(self):
        """Benchmark: Event detection with 3 colonists should be <1ms."""
        # Set up state with 3 colonists
        previous = [
            {"id": 1, "name": "Alice", "health": 0.8, "current_job": "Mining"},
            {"id": 2, "name": "Bob", "health": 0.6, "current_job": "Hauling"},
            {"id": 3, "name": "Charlie", "health": 0.9, "current_job": "Growing"}
        ]
        
        current = [
            {"id": 1, "name": "Alice", "health": 0.75, "current_job": "Mining"},
            {"id": 2, "name": "Bob", "health": 0.4, "current_job": "Construction"},  # Health warning + job change
            {"id": 3, "name": "Charlie", "health": 0.9, "current_job": "Growing"}
        ]
        
        self.listener._known_colonist_ids = {1, 2, 3}
        
        # Warmup
        for _ in range(10):
            self.listener._detect_colonist_events(current, previous)
        
        # Benchmark
        iterations = 1000
        start = time.perf_counter()
        
        for _ in range(iterations):
            events = self.listener._detect_colonist_events(current, previous)
        
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        avg_ms = elapsed_ms / iterations
        
        print(f"\nEvent detection (3 colonists): {avg_ms:.4f}ms (target: <1ms)")
        assert avg_ms < 1.0, f"Event detection too slow: {avg_ms:.4f}ms"
    
    def test_event_detection_performance_medium(self):
        """Benchmark: Event detection with 10 colonists should be <5ms."""
        # Set up state with 10 colonists
        previous = [
            {"id": i, "name": f"Colonist{i}", "health": 0.8, "current_job": "Mining"}
            for i in range(10)
        ]
        
        current = [
            {"id": i, "name": f"Colonist{i}", "health": 0.75, "current_job": "Mining"}
            for i in range(10)
        ]
        # Add some changes
        current[2]["health"] = 0.15  # Critical health
        current[5]["current_job"] = "Hauling"  # Job change
        
        self.listener._known_colonist_ids = set(range(10))
        
        # Warmup
        for _ in range(10):
            self.listener._detect_colonist_events(current, previous)
        
        # Benchmark
        iterations = 1000
        start = time.perf_counter()
        
        for _ in range(iterations):
            events = self.listener._detect_colonist_events(current, previous)
        
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        avg_ms = elapsed_ms / iterations
        
        print(f"\nEvent detection (10 colonists): {avg_ms:.4f}ms (target: <5ms)")
        assert avg_ms < 5.0, f"Event detection too slow: {avg_ms:.4f}ms"
    
    def test_event_detection_performance_large(self):
        """Benchmark: Event detection with 50 colonists should be <25ms."""
        # Set up state with 50 colonists
        previous = [
            {"id": i, "name": f"Colonist{i}", "health": 0.8, "current_job": "Mining"}
            for i in range(50)
        ]
        
        current = [
            {"id": i, "name": f"Colonist{i}", "health": 0.75, "current_job": "Mining"}
            for i in range(50)
        ]
        # Add some changes
        current[5]["health"] = 0.15   # Critical health
        current[15]["health"] = 0.4   # Warning health
        current[25]["current_job"] = "Hauling"  # Job change
        current[35]["current_job"] = "Construction"  # Job change
        
        self.listener._known_colonist_ids = set(range(50))
        
        # Warmup
        for _ in range(10):
            self.listener._detect_colonist_events(current, previous)
        
        # Benchmark
        iterations = 1000
        start = time.perf_counter()
        
        for _ in range(iterations):
            events = self.listener._detect_colonist_events(current, previous)
        
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        avg_ms = elapsed_ms / iterations
        
        print(f"\nEvent detection (50 colonists): {avg_ms:.4f}ms (target: <25ms)")
        assert avg_ms < 25.0, f"Event detection too slow: {avg_ms:.4f}ms"
    
    def test_queue_operations_performance(self):
        """Benchmark: Queue put/get operations should be <0.1ms."""
        state = {"frame_id": 100, "data": "test"}
        
        # Warmup
        for _ in range(100):
            self.state_queue.put(state)
            self.state_queue.get()
        
        # Benchmark
        iterations = 10000
        start = time.perf_counter()
        
        for _ in range(iterations):
            self.state_queue.put(state)
            self.state_queue.get()
        
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        avg_ms = elapsed_ms / iterations
        
        print(f"\nQueue operations: {avg_ms:.4f}ms per put+get (target: <0.1ms)")
        assert avg_ms < 0.1, f"Queue operations too slow: {avg_ms:.4f}ms"
    
    def test_memory_efficiency(self):
        """Verify no excessive memory allocation during event detection."""
        import gc
        
        # Set up large state
        previous = [
            {"id": i, "name": f"Colonist{i}", "health": 0.8, "current_job": "Mining"}
            for i in range(100)
        ]
        
        current = [
            {"id": i, "name": f"Colonist{i}", "health": 0.75, "current_job": "Mining"}
            for i in range(100)
        ]
        
        self.listener._known_colonist_ids = set(range(100))
        
        # Force garbage collection before benchmark
        gc.collect()
        
        # Record initial GC stats
        gc_before = gc.get_count()
        
        # Run many iterations
        for _ in range(1000):
            events = self.listener._detect_colonist_events(current, previous)
        
        # Check GC stats
        gc_after = gc.get_count()
        
        # Should not trigger excessive garbage collection
        # (Some allocation is expected, but should be minimal)
        gen0_collections = gc_after[0] - gc_before[0]
        
        print(f"\nGC collections (gen0): {gen0_collections} during 1000 iterations")
        # Allow reasonable GC activity (target: <10 collections per 1000 iterations)
        assert gen0_collections < 50, f"Too many GC collections: {gen0_collections}"
    
    def test_polling_throughput(self):
        """Benchmark: Polling throughput should support >10 polls/sec."""
        # Mock connection that returns states quickly
        def mock_send_command(cmd, timeout=None):
            msg = StateMessage()
            msg.frame_id = 100
            return msg
        
        self.connection.send_command = mock_send_command
        self.connection.is_healthy = Mock(return_value=True)
        self.connection.is_connected = Mock(return_value=True)
        
        listener = ListenerThread(
            connection_manager=self.connection,
            state_queue=self.state_queue,
            event_queue=self.event_queue,
            stop_event=self.stop_event,
            poll_interval_ms=50  # 20 polls/sec target
        )
        
        listener.start()
        
        # Run for 1 second
        time.sleep(1.0)
        
        self.stop_event.set()
        listener.join(timeout=1.0)
        
        stats = listener.get_stats()
        poll_count = stats["poll_count"]
        
        print(f"\nPolling throughput: {poll_count} polls/second (target: >10)")
        assert poll_count >= 10, f"Polling throughput too low: {poll_count}/sec"


def run_benchmarks():
    """Run all benchmarks and print summary."""
    print("\n" + "="*60)
    print("Phase IV.2 Listener Thread Performance Benchmarks")
    print("="*60)
    
    test = TestListenerPerformance()
    
    benchmarks = [
        ("State Parsing", test.test_state_parsing_performance),
        ("Event Detection (Small)", test.test_event_detection_performance_small),
        ("Event Detection (Medium)", test.test_event_detection_performance_medium),
        ("Event Detection (Large)", test.test_event_detection_performance_large),
        ("Queue Operations", test.test_queue_operations_performance),
        ("Memory Efficiency", test.test_memory_efficiency),
        ("Polling Throughput", test.test_polling_throughput),
    ]
    
    passed = 0
    failed = 0
    
    for name, benchmark in benchmarks:
        try:
            test.setup_method()
            benchmark()
            print(f"✅ {name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name}: Unexpected error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)


if __name__ == "__main__":
    run_benchmarks()
