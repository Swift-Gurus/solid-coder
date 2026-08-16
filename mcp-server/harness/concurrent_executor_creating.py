"""Defines creation of bounded concurrent executors."""

from __future__ import annotations

from concurrent.futures import Executor
from typing import Protocol


"""
solid-name: ConcurrentExecutorCreating
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for creating an executor with a requested worker bound.
"""
class ConcurrentExecutorCreating(Protocol):
    def create(self, max_workers: int) -> Executor: ...
