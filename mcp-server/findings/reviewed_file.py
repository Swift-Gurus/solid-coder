"""Defines one immutable file in a review submission."""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from findings.review_unit import ReviewUnit


"""
solid-name: ReviewedFile
solid-category: model
solid-description: Represents one reviewed file and its immutable source-code units.
"""
@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class ReviewedFile:
    file_path: str
    units: tuple[ReviewUnit, ...]
