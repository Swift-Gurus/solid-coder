"""
solid-name: ForEachReferenceValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates that each step's for_each expression references an existing step and one of its declared outputs.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowValidationError, StepDef


class ForEachReferenceValidating(Protocol):

    def validate_for_each_references(self, steps: list[StepDef]) -> None: ...


class ForEachReferenceValidator(ForEachReferenceValidating):

    def validate_for_each_references(self, steps: list[StepDef]) -> None:
        step_outputs: dict[str, set[str]] = {
            step.id: {o.name for o in step.outputs}
            for step in steps
        }

        for step in steps:
            if step.for_each is None:
                continue
            expr = step.for_each.strip("{} ")
            parts = expr.split(".")
            if len(parts) >= 4 and parts[0] == "steps" and parts[2] == "outputs":
                dep_step_id = parts[1]
                output_name = parts[3]
                if dep_step_id not in step_outputs:
                    raise FlowValidationError(
                        f"Step '{step.id}' for_each references unknown step '{dep_step_id}'"
                    )
                if output_name not in step_outputs[dep_step_id]:
                    raise FlowValidationError(
                        f"Step '{step.id}' for_each references unknown output '{output_name}' on step '{dep_step_id}'"
                    )
