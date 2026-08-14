"""Validates workflow for-each references."""

from __future__ import annotations

from harness.for_each_reference_parsing import ForEachReferenceParsing
from harness.for_each_reference_validating import ForEachReferenceValidating
from harness.models import FlowValidationError, StepDef
from harness.step_dependency_reachability_checking import StepDependencyReachabilityChecking


"""
solid-name: ForEachReferenceValidator
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Validates workflow iteration syntax, source outputs, array schemas, and dependency reachability.
"""
class ForEachReferenceValidator(ForEachReferenceValidating):
    def __init__(
        self,
        reference_parser: ForEachReferenceParsing,
        reachability_checker: StepDependencyReachabilityChecking,
    ) -> None:
        self._reference_parser = reference_parser
        self._reachability_checker = reachability_checker

    def validate_for_each_references(self, steps: list[StepDef]) -> None:
        for step in steps:
            if step.for_each is None:
                continue
            reference = self._reference_parser.parse(step.id, step.for_each)
            source_step = next(
                (candidate for candidate in steps if candidate.id == reference.step_id),
                None,
            )
            if source_step is None:
                raise FlowValidationError(
                    f"Step '{step.id}' for_each references unknown step '{reference.step_id}'"
                )
            source_output = next(
                (
                    output
                    for output in source_step.outputs
                    if output.name == reference.output_name
                ),
                None,
            )
            if source_output is None:
                raise FlowValidationError(
                    f"Step '{step.id}' for_each references unknown output '{reference.output_name}' "
                    f"on step '{reference.step_id}'"
                )
            if not self._reachability_checker.is_dependency(
                reference.step_id,
                step,
                steps,
            ):
                raise FlowValidationError(
                    f"Step '{step.id}' for_each must reference a transitive dependency"
                )
            if source_output.schema is None or source_output.schema.get("type") != "array":
                raise FlowValidationError(
                    f"Step '{step.id}' for_each source output '{reference.output_name}' "
                    "must declare an array schema"
                )
