"""
solid-description: Measures elapsed wall-clock time.
solid-category: utility
solid-tags: [hook, llm]
"""

import time
from typing import Protocol


class TimeMeasuring(Protocol):
    def now(self) -> float: ...
    def elapsed(self, start: float) -> float: ...


class MonotonicTimer:
    """Boundary adapter: measures elapsed wall-clock time via time.monotonic.

    time.monotonic is a global stdlib function — this adapter satisfies
    the OCP Boundary Adapter exception.
    """

    def now(self) -> float:
        return time.monotonic()

    def elapsed(self, start: float) -> float:
        return self.now() - start
