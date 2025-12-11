"""
Thread-safe queue implementations for RimWorld ML Bridge client.

Provides specialized queues for state, events, and actions with appropriate sizing
and overflow handling.
"""

import queue
import logging
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels for prioritization."""
    CRITICAL = 0  # Under attack, fire spreading
    HIGH = 1      # Raid starting, mental break
    MEDIUM = 2    # Job completion, item hauled
    LOW = 3       # Mood change, need decrease


@dataclass
class PrioritizedItem:
    """Wrapper for priority queue items."""
    priority: int
    item: Any
    
    def __lt__(self, other):
        """Compare by priority (lower number = higher priority)."""
        return self.priority < other.priority


class StateQueue:
    """
    Queue for game state observations from Listener to Inference thread.
    
    Uses FIFO with size limit. Drops oldest states when full.
    """
    
    def __init__(self, maxsize: int = 10):
        """
        Initialize state queue.
        
        Args:
            maxsize: Maximum queue size
        """
        self._queue = queue.Queue(maxsize=maxsize)
        self._maxsize = maxsize
        self._dropped_count = 0
        
        logger.info(f"StateQueue initialized (maxsize={maxsize})")
    
    def put(self, state: Any, timeout: Optional[float] = None) -> bool:
        """
        Put state into queue, dropping oldest if full.
        
        Args:
            state: State object to enqueue
            timeout: Optional timeout (not used for non-blocking)
            
        Returns:
            True if successfully queued, False if dropped
        """
        try:
            self._queue.put_nowait(state)
            return True
        except queue.Full:
            # Drop oldest state and try again
            try:
                old_state = self._queue.get_nowait()
                self._queue.put_nowait(state)
                self._dropped_count += 1
                
                if self._dropped_count % 10 == 0:
                    logger.warning(f"StateQueue full: {self._dropped_count} states dropped")
                
                return True
            except queue.Empty:
                # Race condition, try one more time
                try:
                    self._queue.put_nowait(state)
                    return True
                except queue.Full:
                    self._dropped_count += 1
                    logger.error("StateQueue: Failed to enqueue after drop")
                    return False
    
    def get(self, timeout: Optional[float] = 1.0) -> Optional[Any]:
        """
        Get state from queue with optional timeout.
        
        Args:
            timeout: Timeout in seconds (None = blocking)
            
        Returns:
            State object or None on timeout
        """
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_latest(self) -> Optional[Any]:
        """
        Get latest state, discarding all older states.
        
        Returns:
            Latest state or None if empty
        """
        state = None
        while True:
            try:
                state = self._queue.get_nowait()
            except queue.Empty:
                break
        return state
    
    def qsize(self) -> int:
        """Get approximate queue size."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    @property
    def dropped_count(self) -> int:
        """Get total number of dropped states."""
        return self._dropped_count


class EventQueue:
    """
    Priority queue for events from Listener to Actor thread.
    
    Uses priority-based ordering with size limit.
    """
    
    def __init__(self, maxsize: int = 100):
        """
        Initialize event queue.
        
        Args:
            maxsize: Maximum queue size
        """
        self._queue = queue.PriorityQueue(maxsize=maxsize)
        self._maxsize = maxsize
        self._dropped_count = 0
        
        logger.info(f"EventQueue initialized (maxsize={maxsize})")
    
    def put(self, event: Any, priority: EventPriority = EventPriority.MEDIUM,
            timeout: Optional[float] = None) -> bool:
        """
        Put event into queue with priority.
        
        Args:
            event: Event object to enqueue
            priority: Event priority level
            timeout: Optional timeout
            
        Returns:
            True if successfully queued, False if dropped
        """
        item = PrioritizedItem(priority.value, event)
        
        try:
            if timeout is not None:
                self._queue.put(item, timeout=timeout)
            else:
                self._queue.put_nowait(item)
            return True
        except queue.Full:
            self._dropped_count += 1
            
            if self._dropped_count % 10 == 0:
                logger.warning(f"EventQueue full: {self._dropped_count} events dropped")
            
            return False
    
    def get(self, timeout: Optional[float] = 0.01) -> Optional[Any]:
        """
        Get highest priority event from queue.
        
        Args:
            timeout: Timeout in seconds (None = blocking)
            
        Returns:
            Event object or None on timeout
        """
        try:
            item = self._queue.get(timeout=timeout)
            return item.item if item else None
        except queue.Empty:
            return None
    
    def qsize(self) -> int:
        """Get approximate queue size."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    @property
    def dropped_count(self) -> int:
        """Get total number of dropped events."""
        return self._dropped_count


class ActionQueue:
    """
    Queue for actions from Inference/Actor threads to execution.
    
    Uses FIFO with support for priority insertion (Actor can override).
    """
    
    def __init__(self, maxsize: int = 100):
        """
        Initialize action queue.
        
        Args:
            maxsize: Maximum queue size
        """
        self._queue = queue.Queue(maxsize=maxsize)
        self._maxsize = maxsize
        self._dropped_count = 0
        
        logger.info(f"ActionQueue initialized (maxsize={maxsize})")
    
    def put(self, action: Any, timeout: Optional[float] = None) -> bool:
        """
        Put action into queue.
        
        Args:
            action: Action object to enqueue
            timeout: Optional timeout
            
        Returns:
            True if successfully queued, False if dropped
        """
        try:
            if timeout is not None:
                self._queue.put(action, timeout=timeout)
            else:
                self._queue.put_nowait(action)
            return True
        except queue.Full:
            self._dropped_count += 1
            
            if self._dropped_count % 10 == 0:
                logger.warning(f"ActionQueue full: {self._dropped_count} actions dropped")
            
            return False
    
    def get(self, timeout: Optional[float] = 0.1) -> Optional[Any]:
        """
        Get action from queue.
        
        Args:
            timeout: Timeout in seconds (None = blocking)
            
        Returns:
            Action object or None on timeout
        """
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def qsize(self) -> int:
        """Get approximate queue size."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()
    
    @property
    def dropped_count(self) -> int:
        """Get total number of dropped actions."""
        return self._dropped_count
