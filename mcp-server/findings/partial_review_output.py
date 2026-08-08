"""Defines one immutable partial review output."""

from __future__ import annotations

from dataclasses import dataclass

from findings.reviewed_file import ReviewedFile


"""
solid-name: PartialReviewOutput
solid-category: model
solid-description: Represents an immutable timestamped review result and its reviewed-file collection.
"""
@dataclass(frozen=True)
class PartialReviewOutput:
    timestamp: str
    files: tuple[ReviewedFile, ...]
