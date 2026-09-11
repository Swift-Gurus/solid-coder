"""Defines runtime controls declared on one workflow include."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.condition_declaration import ConditionDeclaration
from harness.for_each_declaration import ForEachDeclaration
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: WorkflowIncludeRuntime
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries group-level dependencies, iteration, input bindings, and eligibility for one workflow include.
"""
@dataclass(frozen=True)
class WorkflowIncludeRuntime:
    depends_on: list[str] = field(default_factory=list)
    for_each: ForEachDeclaration | None = None
    input_bindings: list[WorkflowInputBinding] = field(default_factory=list)
    condition: ConditionDeclaration | None = None
    execution: WorkflowExecutionMode = WorkflowExecutionMode.GRANULAR
    presentation: WorkflowPresentationMode = WorkflowPresentationMode.INDIVIDUAL
