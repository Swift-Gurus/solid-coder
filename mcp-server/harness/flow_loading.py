"""
solid-description: Contract for loading a flow configuration from a file path using provided search paths.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef


class FlowLoading(Protocol):
    """
    solid-description: Contract for loading a flow configuration from a file path using provided search paths.
    solid-category: abstraction
    """

    def load(self, path: str, search_paths: list[str]) -> FlowDef: ...
