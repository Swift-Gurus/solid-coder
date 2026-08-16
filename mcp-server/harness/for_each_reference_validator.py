"""Validates workflow for-each references."""

from __future__ import annotations

from harness.flow_validation_error import FlowValidationError
from harness.for_each_reference_parsing import ForEachReferenceParsing
from harness.for_each_target_validating import ForEachTargetValidating
from harness.models import StepDef
from harness.step_dependency_reachability_checking import (
    StepDependencyReachabilityChecking,
)


"""
solid-name: ForEachReferenceValidator
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Validates workflow iteration syntax, source outputs, array schemas, and dependency reachability.
"""
class ForEachReferenceValidator(ForEachTargetValidating):
    def __init__(
        self,
        reference_parser: ForEachReferenceParsing,
        reachability_checker: StepDependencyReachabilityChecking,
    ) -> None:
        self._reference_parser = reference_parser
        self._reachability_checker = reachability_checker

    def validate(
        self,
        target_id: str,
        for_each: str | None,
        dependency_ids: list[str],
        steps: list[StepDef],
    ) -> None:
        if for_each is None:
            return
        reference = self._reference_parser.parse(target_id, for_each)
        source_step = next(
            (candidate for candidate in steps if candidate.id == reference.step_id),
            None,
        )
        if source_step is None:
            raise FlowValidationError(
                f"Step '{target_id}' for_each references unknown step "
                f"'{reference.step_id}'"
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
                f"Step '{target_id}' for_each references unknown output "
                f"'{reference.output_name}' on step '{reference.step_id}'"
            )
        if not self._reachability_checker.is_dependency(
            reference.step_id,
            dependency_ids,
            steps,
        ):
            raise FlowValidationError(
                f"Step '{target_id}' for_each must reference a transitive dependency"
            )
        if source_output.schema is None or source_output.schema.get("type") != "array":
            raise FlowValidationError(
                f"Step '{target_id}' for_each source output "
                f"'{reference.output_name}' must declare an array schema"
            )
