"""Defines typed output projection across included workflow results."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.workflow_output_values import WorkflowOutputValues


"""
solid-name: WorkflowOutputProjections
solid-category: model
solid-spec: [SPEC-037, SPEC-056]
solid-description: Projects one declared child-workflow output across completed instances in source order.
"""
@dataclass(frozen=True)
class WorkflowOutputProjections:
    declared_names: list[str] = field(default_factory=list)
    entries: list[WorkflowOutputValues] = field(default_factory=list)

    def __getattr__(self, output_name: str) -> list[object]:
        if output_name not in self.declared_names:
            raise AttributeError(output_name)

        values: list[object] = []
        for outputs in self.entries:
            resolved = outputs.find(output_name)
            if not resolved.present:
                raise AttributeError(output_name)
            values.append(resolved.value)
        return values
