"""
solid-name: SubagentDelegating
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for conditionally transforming a string value based on execution state.
"""

from __future__ import annotations

from typing import Protocol


class SubagentDelegating(Protocol):
    def wrap_if_subagent(self, body: str, execution: dict) -> str: ...
