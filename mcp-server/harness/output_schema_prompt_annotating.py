"""
solid-name: OutputSchemaPromptAnnotating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for annotating a step with information derived from its declared output schemas.
"""

from __future__ import annotations

from typing import Protocol


class OutputSchemaPromptAnnotating(Protocol):

    def annotate(self, step: dict) -> dict: ...
