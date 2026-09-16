"""Declares aggregate submission-instruction rendering."""

from typing import Protocol

from harness.aggregate_assignment_recovery_reading import (
    AggregateAssignmentRecoveryReading,
)


"""
solid-name: AggregateSubmissionInstructionRendering
solid-category: abstraction
solid-spec: [SPEC-052]
solid-description: Contract for rendering initial and corrective aggregate submission guidance.
"""
class AggregateSubmissionInstructionRendering(Protocol):
    def render(
        self,
        assignments: list[AggregateAssignmentRecoveryReading],
    ) -> str: ...
