# Producer–Consumer with Bounded Blocking Queue (Python)

This project implements a classic **Producer–Consumer** pattern using:

- A custom **bounded blocking queue**
- **Thread synchronization** with `Lock` + `Condition`
- A **wait/notify** mechanism for coordinating producer and consumer threads
- A clean, testable design with **unit tests**

---

## Features

### `BoundedBlockingQueue[T]`

- Thread-safe, bounded queue
- `put()` blocks when the queue is **full**
- `get()` blocks when the queue is **empty**
- Uses `Condition.wait()` / `Condition.notify()` internally
- Provides helper methods:
  - `size()`
  - `empty()`
  - `full()`

### `Producer[T]`

- Subclass of `threading.Thread`
- Reads from a source container (`Iterable[T]`)
- Pushes items into the shared blocking queue
- After producing all items, pushes a **sentinel** to signal completion

### `Consumer[T]`

- Subclass of `threading.Thread`
- Continuously reads items from the shared queue
- Appends real items into a destination container (`List[T]`)
- Stops when it reads the sentinel (and does **not** store it)

### `run_pipeline(...)`

- Convenience function that wires together:
  - One `Producer`
  - One `Consumer`
  - One `BoundedBlockingQueue`
- Starts both threads, waits for them to finish, then returns the destination container

---

## Project Structure

```text
.
├── producer_consumer.py        # Core implementation (queue, producer, consumer, pipeline)
└── test_producer_consumer.py   # Unit tests for queue + pipeline behavior
```

## Requirements

- Python **3.8+**

The project uses only the Python standard library:

- `threading`
- `collections.deque`
- `unittest`
- `typing`

No external dependencies are required.

---

## How It Works (High-Level)

### 1. `BoundedBlockingQueue`

The queue:

- Stores items in an internal `deque`
- Uses a single `Lock` to protect access
- Uses two `Condition` variables bound to the same lock:
  - `_not_empty` – for consumers to wait when the queue is empty  
  - `_not_full` – for producers to wait when the queue is full  

This design enforces proper thread synchronization and ensures producers/consumers block instead of busy-waiting.

---

### 2. Sentinel

A **sentinel** is a special value pushed to the queue to signal that no more real data will be produced.

The sentinel:

- Is **not** written into the destination list
- Is compared using `is` (identity) to ensure it’s that exact object
- Allows the consumer thread to know when to stop cleanly without relying on timeouts or magic values

---

## How to Run the Code

Make sure you are in the directory containing `producer_consumer.py`.

### Option 1: Run interactively in Python (recommended for this project)


```bash
python

from producer_consumer import run_pipeline

result_ints = run_pipeline(range(10), queue_maxsize=3)
print("Int result:", result_ints)

result_strings = run_pipeline(["alpha", "beta", "gamma"], queue_maxsize=2)
print("String result:", result_strings)
```

You should see the same items in the same order in the printed lists.

### Option 2: Add a small demo inside producer_consumer.py (optional)

At the bottom of producer_consumer.py, you can add:

```python
if __name__ == "__main__":
    from producer_consumer import run_pipeline

    source = list(range(10))
    result = run_pipeline(source, queue_maxsize=3)
    print("Source:     ", source)
    print("Destination:", result)
```

Then run:

```bash
python producer_consumer.py
```


## How to Run the tests

Make sure test_producer_consumer.py is in the same directory as producer_consumer.py.

To run all unit tests:

```bash
python -m unittest -v
```

The tests will:
-	Verify basic queue operations in a single thread
-	Check correct item ordering under concurrent producer/consumer
-	Validate blocking behavior when the queue is full/empty
-	Confirm proper sentinel handling and thread termination
-	Check that invalid parameters (e.g., queue_maxsize <= 0) raise ValueError
-   If everything is correct, all tests will be reported as ok.