"""Defines persisted payload construction for reviewed files."""

from typing import Protocol

from findings.reviewed_file import ReviewedFile


"""
solid-name: ReviewedFilePayloadBuilding
solid-category: abstraction
solid-description: Contract for constructing the persisted payload for one reviewed file.
"""
class ReviewedFilePayloadBuilding(Protocol):
    def build(self, reviewed_file: ReviewedFile) -> dict: ...
