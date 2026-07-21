"""
solid-name: FlowFileResolving
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for resolving a flow identifier to its file path.
"""

from __future__ import annotations

from typing import Protocol


class FlowFileResolving(Protocol):

    def resolve(self, flow: str, search_paths: list[str]) -> str: ...
