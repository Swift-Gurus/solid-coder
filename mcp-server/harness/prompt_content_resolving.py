"""
solid-name: PromptContentResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving prompt content for a step.
"""

from __future__ import annotations

from typing import Protocol


class PromptContentResolving(Protocol):

    def resolve(self, step: dict, flow_file_path: str) -> dict: ...