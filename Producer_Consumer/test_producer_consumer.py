import time
import unittest
from typing import List

from producer_consumer import (
    BoundedBlockingQueue,
    run_pipeline,
    Producer,
    Consumer,
)


class TestBoundedBlockingQueue(unittest.TestCase):
    def test_put_and_get_single_thread(self) -> None:
        q: BoundedBlockingQueue[int] = BoundedBlockingQueue(maxsize=3)

        q.put(1)
        q.put(2)
        q.put(3)

        self.assertEqual(q.size(), 3)
        self.assertTrue(q.full())

        self.assertEqual(q.get(), 1)
        self.assertEqual(q.get(), 2)
        self.assertEqual(q.get(), 3)
        self.assertTrue(q.empty())

    def test_invalid_maxsize_raises(self) -> None:
        with self.assertRaises(ValueError):
            BoundedBlockingQueue(0)

    def test_concurrent_producer_consumer_respects_order(self) -> None:
        q: BoundedBlockingQueue[int] = BoundedBlockingQueue(maxsize=2)

        produced: List[int] = list(range(20))
        consumed: List[int] = []

        def producer() -> None:
            for value in produced:
                q.put(value)

        def consumer() -> None:
            for _ in produced:
                consumed.append(q.get())

        from threading import Thread

        t_producer = Thread(target=producer)
        t_consumer = Thread(target=consumer)

        t_producer.start()
        t_consumer.start()

        t_producer.join(timeout=3)
        t_consumer.join(timeout=3)

        self.assertEqual(consumed, produced)
        self.assertTrue(q.empty())

    def test_queue_blocks_when_full_and_empties_properly(self) -> None:
        """
        Small concurrency test that stresses the 'full' state.
        Validates that:
        - queue size never exceeds maxsize
        - queue ends up empty
        """
        q: BoundedBlockingQueue[int] = BoundedBlockingQueue(maxsize=1)
        observed_sizes: List[int] = []

        def producer() -> None:
            # Push a few items quickly so we hit the "full" state
            for i in range(3):
                q.put(i)
                observed_sizes.append(q.size())

        def consumer() -> None:
            # Let producer run and possibly block
            time.sleep(0.1)
            for _ in range(3):
                time.sleep(0.05)
                q.get()

        from threading import Thread

        t_producer = Thread(target=producer)
        t_consumer = Thread(target=consumer)

        t_producer.start()
        t_consumer.start()

        t_producer.join(timeout=3)
        t_consumer.join(timeout=3)

        self.assertTrue(q.empty())
        # Queue capacity is 1, so we should never observe size > 1
        self.assertTrue(all(size <= 1 for size in observed_sizes))


class TestProducerConsumerPipeline(unittest.TestCase):
    def test_run_pipeline_transfers_all_items(self) -> None:
        source = list(range(100))
        destination = run_pipeline(source, queue_maxsize=5)
        self.assertEqual(destination, source)

    def test_run_pipeline_with_strings(self) -> None:
        source = ["alpha", "beta", "gamma", "delta"]
        destination = run_pipeline(source, queue_maxsize=2)
        self.assertEqual(destination, source)

    def test_run_pipeline_empty_source(self) -> None:
        source: List[int] = []
        destination = run_pipeline(source, queue_maxsize=3)
        self.assertEqual(destination, [])

    def test_run_pipeline_multiple_times(self) -> None:
        """
        Ensure the pipeline is repeatable and has no hidden global state issues.
        """
        source = [1, 2, 3, 4, 5]
        for _ in range(5):
            destination = run_pipeline(source, queue_maxsize=2)
            self.assertEqual(destination, source)

    def test_run_pipeline_invalid_maxsize(self) -> None:
        """
        run_pipeline should surface the same ValueError as BoundedBlockingQueue
        when an invalid queue_maxsize is passed.
        """
        with self.assertRaises(ValueError):
            run_pipeline([1, 2, 3], queue_maxsize=0)


class TestProducerConsumerSentinel(unittest.TestCase):
    def test_sentinel_not_in_destination_and_consumer_stops(self) -> None:
        """
        Explicitly test that:
        - All real items are transferred to destination
        - Sentinel is *not* stored in destination
        - Producer and consumer both terminate
        """
        queue: BoundedBlockingQueue[int | object] = BoundedBlockingQueue(maxsize=2)
        destination: List[int] = []
        sentinel = object()

        producer = Producer([1, 2, 3], queue, sentinel, name="TestProducer")
        consumer = Consumer(queue, destination, sentinel, name="TestConsumer")

        producer.start()
        consumer.start()

        producer.join(timeout=3)
        consumer.join(timeout=3)

        # Sentinel should never appear in the destination
        self.assertEqual(destination, [1, 2, 3])
        self.assertFalse(producer.is_alive())
        self.assertFalse(consumer.is_alive())


if __name__ == "__main__":
    unittest.main()