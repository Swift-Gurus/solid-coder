"""Maps ordered items through an injected bounded executor."""

from __future__ import annotations

from typing import Callable, TypeVar

from harness.concurrent_executor_creating import ConcurrentExecutorCreating
from harness.concurrent_item_mapping import ConcurrentItemMapping


Input = TypeVar("Input")
Output = TypeVar("Output")


"""
solid-name: ExecutorItemMapper
solid-category: service
solid-spec: [SPEC-037]
solid-description: Applies one operation concurrently to ordered items within a supplied worker bound.
"""
class ExecutorItemMapper(ConcurrentItemMapping):
    def __init__(self, executor_factory: ConcurrentExecutorCreating) -> None:
        self._executor_factory = executor_factory

    def map(
        self,
        operation: Callable[[Input], Output],
        items: list[Input],
        max_workers: int,
    ) -> list[Output]:
        if max_workers < 1:
            raise ValueError("Concurrent item max_workers must be at least 1")
        if not items:
            return []
        worker_count = min(max_workers, len(items))
        with self._executor_factory.create(worker_count) as executor:
            futures = [executor.submit(operation, item) for item in items]
            return [future.result() for future in futures]
