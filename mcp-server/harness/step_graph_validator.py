"""Validates workflow-step dependency graphs."""

from __future__ import annotations

from harness.cycle_detecting import CycleDetecting
from harness.dependency_graph_validating import DependencyGraphValidating
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_group import IncludeAliasGroup
from harness.step_dependency_graph_creating import StepDependencyGraphCreating
from harness.unique_step_identity_validating import UniqueStepIdentityValidating


"""
solid-name: StepGraphValidator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Validates workflow-step identities, dependencies, and dependency cycles.
"""
class StepGraphValidator(DependencyGraphValidating):

    def __init__(
        self,
        identity_validator: UniqueStepIdentityValidating,
        graph_factory: StepDependencyGraphCreating,
        cycle_detector: CycleDetecting,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._identity_validator = identity_validator
        self._graph_factory = graph_factory
        self._cycle_detector = cycle_detector
        self._error_factory = error_factory

    def validate(
        self,
        steps: list[GraphStepFieldReading],
        alias_groups: list[IncludeAliasGroup] | None = None,
    ) -> None:
        self._identity_validator.validate(steps)
        graph = self._graph_factory.create(steps, alias_groups or [])
        if self._cycle_detector.has_cycle(graph):
            raise self._error_factory.create("Dependency cycle detected in flow steps")
