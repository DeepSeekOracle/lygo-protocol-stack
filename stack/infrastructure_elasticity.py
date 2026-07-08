"""Phase 1 — Infrastructure Elasticity: priority queue + mycelium batching."""

from __future__ import annotations

import heapq
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(order=True)
class _QueuedItem:
    priority: int
    seq: int
    payload: dict = field(compare=False)
    key: str = field(compare=False)
    callback: Callable[[dict, str], Any] | None = field(compare=False, default=None)


class PriorityEthicalQueue:
    """Higher priority = lower numeric rank (QUARANTINE-path audits first)."""

    PRIORITY_MAP = {
        "QUARANTINE": 0,
        "SOFTEN": 5,
        "AMPLIFY": 10,
        "default": 7,
    }

    def __init__(self) -> None:
        self._heap: list[_QueuedItem] = []
        self._seq = 0
        self._lock = threading.Lock()

    def enqueue(
        self,
        payload: dict,
        key: str,
        *,
        verdict_hint: str = "default",
        callback: Callable[[dict, str], Any] | None = None,
    ) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        pri = self.PRIORITY_MAP.get(verdict_hint.upper(), self.PRIORITY_MAP["default"])
        with self._lock:
            self._seq += 1
            heapq.heappush(
                self._heap,
                _QueuedItem(pri, self._seq, {**payload, "job_id": job_id}, key, callback),
            )
        return job_id

    def dequeue_batch(self, max_items: int = 32) -> list[_QueuedItem]:
        batch: list[_QueuedItem] = []
        with self._lock:
            while self._heap and len(batch) < max_items:
                batch.append(heapq.heappop(self._heap))
        return batch

    def pending(self) -> int:
        with self._lock:
            return len(self._heap)


class MyceliumBatchWriter:
    """Batch scatter() calls into P1 mycelium for throughput under load."""

    def __init__(self, mycelium: Any, *, batch_size: int = 16, flush_interval_s: float = 0.5) -> None:
        self.mycelium = mycelium
        self.batch_size = batch_size
        self.flush_interval_s = flush_interval_s
        self._buffer: list[tuple[dict, str]] = []
        self._lock = threading.Lock()
        self._last_flush = time.monotonic()
        self.stats = {"flushed_batches": 0, "records": 0}

    def add(self, record: dict, key: str) -> None:
        with self._lock:
            self._buffer.append((record, key))
            if len(self._buffer) >= self.batch_size:
                self._flush_locked()

    def flush(self) -> int:
        with self._lock:
            return self._flush_locked()

    def _flush_locked(self) -> int:
        if not self._buffer:
            return 0
        chunk = self._buffer[:]
        self._buffer.clear()
        self._last_flush = time.monotonic()
        for record, key in chunk:
            self.mycelium.scatter(record, key)
        self.stats["flushed_batches"] += 1
        self.stats["records"] += len(chunk)
        return len(chunk)

    def maybe_flush(self) -> int:
        if time.monotonic() - self._last_flush >= self.flush_interval_s:
            return self.flush()
        return 0


class ElasticityCoordinator:
    """Phase 1 coordinator — queue + batch writer for stack hot paths."""

    version = "Δ9Φ963-PHASE1-ELASTICITY-v1"

    def __init__(self, mycelium: Any, *, batch_size: int = 16) -> None:
        self.queue = PriorityEthicalQueue()
        self.batcher = MyceliumBatchWriter(mycelium, batch_size=batch_size)

    def scatter_prioritized(self, record: dict, key: str, *, verdict_hint: str = "default") -> str:
        job_id = self.queue.enqueue(record, key, verdict_hint=verdict_hint)
        self.batcher.add({**record, "job_id": job_id}, key)
        self.batcher.maybe_flush()
        return job_id

    def drain_queue_to_mycelium(self, max_items: int = 64) -> dict:
        items = self.queue.dequeue_batch(max_items)
        for item in items:
            self.batcher.add(item.payload, item.key)
        n = self.batcher.flush()
        return {"dequeued": len(items), "flushed_records": n, "pending": self.queue.pending()}

    def status(self) -> dict:
        return {
            "version": self.version,
            "pending_jobs": self.queue.pending(),
            "batcher_stats": dict(self.batcher.stats),
        }


if __name__ == "__main__":
    print(json.dumps({"module": "infrastructure_elasticity", "phase": 1, "ok": True}))