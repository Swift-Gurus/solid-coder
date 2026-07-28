"""
solid-name: DelegateInstructionBuilding
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for augmenting text with additional content.
"""

from __future__ import annotations

from typing import Protocol


class DelegateInstructionBuilding(Protocol):

    def build(self, prompt: str) -> str: ...
