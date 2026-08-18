"""Defines collection of named step outputs for schema validation."""

from typing import Protocol

from harness.flow_def import FlowDef
from harness.step_instance import StepInstance
from harness.step_output_submission import StepOutputSubmission


"""
solid-name: StepOutputSubmissionCollecting
solid-category: abstraction
solid-spec: [SPEC-031, SPEC-039]
solid-description: Contract for collecting typed output submissions from ready workflow instances.
"""
class StepOutputSubmissionCollecting(Protocol):
    def collect(
        self,
        ready: list[StepInstance],
        outputs: dict,
        flow_def: FlowDef,
    ) -> list[StepOutputSubmission]: ...
