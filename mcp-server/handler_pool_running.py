"""
solid-name: HandlerPoolRunning
solid-category: abstraction
solid-description: Contract for applying a function to each item in a list and returning the results in order.
solid-tags: [hook]
"""

from typing import Callable, List, Protocol, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class HandlerPoolRunning(Protocol):
    def map(self, fn: Callable[[T], R], items: List[T]) -> List[R]: ...
