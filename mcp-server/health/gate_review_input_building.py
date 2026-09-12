"""Defines prospective gate review-input construction."""

from __future__ import annotations

from typing import Protocol

from patch_review_context import PatchReviewContext
from review.prepare_review_input import PrepareReviewInput


"""
solid-name: GateReviewInputBuilding
solid-category: abstraction
solid-spec: [SPEC-036, SPEC-041]
solid-description: Contract for converting one prospective gate request into typed review preparation input.
"""
class GateReviewInputBuilding(Protocol):
    def build(
        self,
        content: str,
        path: str,
        patch_context: PatchReviewContext | None,
    ) -> PrepareReviewInput: ...
