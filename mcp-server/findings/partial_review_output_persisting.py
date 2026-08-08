"""Defines persistence of typed review outputs."""

from pathlib import Path
from typing import Protocol

from findings.partial_review_output import PartialReviewOutput


"""
solid-name: PartialReviewOutputPersisting
solid-category: abstraction
solid-description: Contract for persisting one scored immutable review output at a requested path.
"""
class PartialReviewOutputPersisting(Protocol):
    def persist(self, output: PartialReviewOutput, output_path: Path) -> None: ...
