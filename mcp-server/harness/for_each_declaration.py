"""Defines one typed workflow iteration declaration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from harness.for_each_mode import ForEachMode
from harness.step_output_reference import StepOutputReference
from harness.workflow_expression import WorkflowExpression


"""
solid-name: ForEachDeclaration
solid-category: model
solid-spec: [SPEC-030, SPEC-042]
solid-description: Carries one typed iteration source plus its model presentation mode and optional domain label expression.
"""
@dataclass(frozen=True)
class ForEachDeclaration:
    source: StepOutputReference
    mode: ForEachMode = ForEachMode.INDIVIDUAL
    label: Optional[WorkflowExpression] = None
