"""Constructs bounded standard-library concurrent executors."""

from __future__ import annotations

from concurrent.futures import Executor, ThreadPoolExecutor

from harness.concurrent_executor_creating import ConcurrentExecutorCreating


"""
solid-name: ThreadPoolExecutorFactory
solid-category: factory
solid-spec: [SPEC-037]
solid-description: Creates bounded concurrent executors for independent workflow work.
"""
class ThreadPoolExecutorFactory(ConcurrentExecutorCreating):
    def create(self, max_workers: int) -> Executor:
        return ThreadPoolExecutor(max_workers=max_workers)
