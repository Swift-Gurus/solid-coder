"""
solid-name: ThreadPoolHandlerRunner
solid-category: service
solid-description: Applies a function to each item in a list concurrently and collects the results.
solid-tags: [hook]
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, TypeVar

from handler_pool_running import HandlerPoolRunning

T = TypeVar("T")
R = TypeVar("R")


class ThreadPoolHandlerRunner(HandlerPoolRunning):
    def map(self, fn: Callable[[T], R], items: List[T]) -> List[R]:
        if not items:
            return []
        with ThreadPoolExecutor(max_workers=len(items)) as pool:
            futures = [pool.submit(fn, item) for item in items]
            return [f.result() for f in futures]
