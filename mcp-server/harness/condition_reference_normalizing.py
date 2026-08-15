"""Defines workflow condition reference normalization."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: ConditionReferenceNormalizing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for normalizing workflow condition references into expression syntax.
"""
class ConditionReferenceNormalizing(Protocol):
    def normalize(self, reference: str) -> str: ...
