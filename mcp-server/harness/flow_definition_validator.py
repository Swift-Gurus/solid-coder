"""Validates resolved and assembled workflow definitions."""

from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.command_allowlist_validating import CommandAllowlistValidating
from harness.dependency_graph_validating import DependencyGraphValidating
from harness.flow_def import FlowDef
from harness.for_each_reference_validating import ForEachReferenceValidating
from harness.include_structure_validator import IncludeStructureValidator
from harness.step_shape_validating import StepShapeValidating


"""
solid-name: FlowDefinitionValidator
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Applies shape, command, graph, include, and executable-reference checks at their valid stages.
"""
class FlowDefinitionValidator:

    def __init__(
        self,
        step_shape_validator: StepShapeValidating,
        command_allowlist_resolver: CommandAllowlistResolving,
        command_allowlist_validator: CommandAllowlistValidating,
        dependency_validator: DependencyGraphValidating,
        include_validator: IncludeStructureValidator,
        for_each_validator: ForEachReferenceValidating,
    ) -> None:
        self._step_shape_validator = step_shape_validator
        self._command_allowlist_resolver = command_allowlist_resolver
        self._command_allowlist_validator = command_allowlist_validator
        self._dependency_validator = dependency_validator
        self._include_validator = include_validator
        self._for_each_validator = for_each_validator

    def validate_resolved(self, definition: FlowDef) -> None:
        self._step_shape_validator.validate(definition.step_declarations)
        allowlist = self._command_allowlist_resolver.resolve()
        self._command_allowlist_validator.validate(definition.step_declarations, allowlist)
        self._dependency_validator.validate(
            definition.step_declarations,
            definition.alias_groups,
        )
        self._include_validator.validate_includes(
            definition.step_declarations,
            definition.alias_groups,
            definition.top_level_step_ids,
            definition.include_chain,
        )

    def validate_assembled(self, flow: FlowDef) -> None:
        self._for_each_validator.validate_for_each_references(flow.steps)
