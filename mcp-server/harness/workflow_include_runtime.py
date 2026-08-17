"""Defines runtime controls declared on one workflow include."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.condition_declaration import ConditionDeclaration
from harness.step_output_reference import StepOutputReference
from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: WorkflowIncludeRuntime
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries group-level dependencies, iteration, input bindings, and eligibility for one workflow include.
"""
@dataclass(frozen=True)
class WorkflowIncludeRuntime:
    depends_on: list[str] = field(default_factory=list)
    for_each: StepOutputReference | None = None
    input_bindings: list[WorkflowInputBinding] = field(default_factory=list)
    condition: ConditionDeclaration | None = None
