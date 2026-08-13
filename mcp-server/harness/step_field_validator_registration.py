"""Associates a workflow-step type with its field validator."""

from __future__ import annotations

from dataclasses import dataclass

from harness.step_field_validating import StepFieldValidating


"""
solid-name: StepFieldValidatorRegistration
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Associates a workflow-step type with its field-validation capability.
"""
@dataclass(frozen=True)
class StepFieldValidatorRegistration:
    step_type: str
    validator: StepFieldValidating
