"""Defines invalidation of DRY-search completion proof."""

from typing import Protocol


"""
solid-name: DrySearchCompletionClearing
solid-category: abstraction
solid-description: Contract for invalidating DRY-search completion before a new health check.
"""
class DrySearchCompletionClearing(Protocol):
    def clear(self, output_dir: str) -> None: ...
