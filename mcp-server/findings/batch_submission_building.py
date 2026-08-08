"""Defines construction of an immutable findings batch submission."""

from typing import Protocol

from findings.batch_submission import BatchSubmission


"""
solid-name: BatchSubmissionBuilding
solid-category: abstraction
solid-description: Contract for constructing an immutable batch submission from a validated external payload.
"""
class BatchSubmissionBuilding(Protocol):
    def build(self, validated_payload: object) -> BatchSubmission: ...
