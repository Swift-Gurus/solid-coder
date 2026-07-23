"""
solid-name: StepSubmissionValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for validating a step's submitted outputs against the declared schema.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, StepInstance, ValidationResult


class StepSubmissionValidating(Protocol):

    def validate(self, step_instance: StepInstance, outputs: dict, flow_def: FlowDef) -> ValidationResult: ...