"""Defines one declared reusable-workflow output."""

from __future__ import annotations

from dataclasses import dataclass

from harness.output_spec import OutputSpec
from harness.step_output_reference import StepOutputReference


"""
solid-name: WorkflowOutputDeclaration
solid-category: model
solid-spec: [SPEC-037]
solid-description: Associates a workflow output specification with its normalized internal step-output reference.
"""
@dataclass(frozen=True)
class WorkflowOutputDeclaration:
    specification: OutputSpec
    reference: StepOutputReference
