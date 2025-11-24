from __future__ import annotations

from collections import deque
from threading import Thread, Condition, Lock
from typing import Deque, Generic, Iterable, List, TypeVar

T = TypeVar("T")


class BoundedBlockingQueue(Generic[T]):
    """
    Thread-safe bounded blocking queue.

    - put() blocks when the queue is full.
    - get() blocks when the queue is empty.
    - Uses wait/notify via Condition variables.
    """

    def __init__(self, maxsize: int) -> None:
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")

        self._maxsize: int = maxsize
        self._queue: Deque[T] = deque()
        """Thread Synchronization Primitives"""
        self._lock: Lock = Lock()
        self._not_empty: Condition = Condition(self._lock)
        self._not_full: Condition = Condition(self._lock)

    def put(self, item: T) -> None:
        """Put item into the queue, blocking if the queue is full."""
        with self._not_full:
            """Blocking Queues"""
            while len(self._queue) >= self._maxsize:
                self._not_full.wait()
            self._queue.append(item)
            # Notify one waiting consumer that an item is available
            self._not_empty.notify()

    def get(self) -> T:
        """Remove and return an item from the queue, blocking if empty."""
        with self._not_empty:
            """Blocking Queues"""
            while not self._queue:
                self._not_empty.wait()
            item = self._queue.popleft()
            # Notify one waiting producer that space is available
            self._not_full.notify()
            return item

    def size(self) -> int:
        """Current number of items (non-blocking, for diagnostics/tests)."""
        with self._lock:
            return len(self._queue)

    def empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0

    def full(self) -> bool:
        with self._lock:
            return len(self._queue) >= self._maxsize

"""Concurrent Producer-Consumer Pipeline Implementation"""
class Producer(Thread, Generic[T]):
    """
    Producer thread:
    - Reads data from a source container (Iterable[T])
    - Pushes items into the shared blocking queue
    - After finishing, sends a sentinel to signal completion
    """

    def __init__(
        self,
        source: Iterable[T],
        queue: BoundedBlockingQueue[T | object],
        sentinel: object,
        *,
        name: str = "Producer",
        daemon: bool = False,
    ) -> None:
        super().__init__(name=name, daemon=daemon)
        # Snapshot input to avoid concurrent mutation from outside
        self._source = list(source)
        self._queue = queue
        self._sentinel = sentinel

    def run(self) -> None:
        for item in self._source:
            self._queue.put(item)
        # Signal to consumer that production is done
        self._queue.put(self._sentinel)

"""Concurrent Producer-Consumer Pipeline Implementation"""
class Consumer(Thread, Generic[T]):
    """
    Consumer thread:
    - Reads items from the shared blocking queue
    - Writes them into a destination container (list by default)
    - Stops when it observes the sentinel
    """

    def __init__(
        self,
        queue: BoundedBlockingQueue[T | object],
        destination: List[T],
        sentinel: object,
        *,
        name: str = "Consumer",
        daemon: bool = False,
    ) -> None:
        super().__init__(name=name, daemon=daemon)
        self._queue = queue
        self._destination = destination
        self._sentinel = sentinel

    def run(self) -> None:
        while True:
            item = self._queue.get()
            if item is self._sentinel:
                # Stop consuming when sentinel is seen
                break
            # Simulate writing to a destination container
            self._destination.append(item)


def run_pipeline(
    source_container: Iterable[T],
    *,
    queue_maxsize: int = 10,
) -> List[T]:
    """
    Convenience function:
      - Creates the shared queue
      - Starts one producer and one consumer
      - Returns the filled destination container.

    This is the end-to-end producer-consumer pipeline.
    """
    queue: BoundedBlockingQueue[T | object] = BoundedBlockingQueue(queue_maxsize)
    destination_container: List[T] = []

    sentinel = object()

    producer = Producer(source_container, queue, sentinel, name="ProducerThread")
    consumer = Consumer(queue, destination_container, sentinel, name="ConsumerThread")

    producer.start()
    consumer.start()

    producer.join()
    consumer.join()

    return destination_container