"""Validates resolved and assembled workflow definitions."""

from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.command_allowlist_validating import CommandAllowlistValidating
from harness.flow_def import FlowDef
from harness.flow_graph_validator import FlowGraphValidating
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
        graph_validator: FlowGraphValidating,
    ) -> None:
        self._step_shape_validator = step_shape_validator
        self._command_allowlist_resolver = command_allowlist_resolver
        self._command_allowlist_validator = command_allowlist_validator
        self._graph_validator = graph_validator

    def validate_resolved(self, definition: FlowDef) -> None:
        self._step_shape_validator.validate(definition.raw_steps)
        allowlist = self._command_allowlist_resolver.resolve()
        self._command_allowlist_validator.validate(definition.raw_steps, allowlist)
        self._graph_validator.validate_raw(definition.raw_steps, definition.alias_groups)
        self._graph_validator.validate_includes(
            definition.raw_steps,
            definition.alias_groups,
            definition.top_level_step_ids,
            definition.include_chain,
        )

    def validate_assembled(self, flow: FlowDef) -> None:
        self._graph_validator.validate_for_each_references(flow.steps)
