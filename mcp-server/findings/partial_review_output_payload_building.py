"""Defines persisted payload construction for scored review outputs."""

from typing import Protocol

from findings.partial_review_output import PartialReviewOutput


"""
solid-name: PartialReviewOutputPayloadBuilding
solid-category: abstraction
solid-description: Contract for constructing persisted payloads from scored review outputs.
"""
class PartialReviewOutputPayloadBuilding(Protocol):
    def build(self, output: PartialReviewOutput) -> dict: ...
