"""Defines rendering of immutable review outputs."""

from typing import Protocol

from findings.partial_review_output import PartialReviewOutput


"""
solid-name: PartialReviewOutputRendering
solid-category: abstraction
solid-description: Contract for rendering a scored immutable review output into persistable text.
"""
class PartialReviewOutputRendering(Protocol):
    def render(self, output: PartialReviewOutput) -> str: ...
