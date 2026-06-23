"""
solid-description: Contract that defines review result collection for pipeline handlers.
solid-category: abstraction
solid-tags: [pipeline]
"""

from typing import Protocol


class ReviewResultsCollecting(Protocol):
    def collect(self, output_root: str) -> dict: ...
