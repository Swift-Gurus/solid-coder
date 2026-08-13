"""Creates typed workflow-step dependency graphs."""

from harness.directed_graph import DirectedGraph
from harness.directed_graph_creating import DirectedGraphCreating
from harness.directed_graph_edge import DirectedGraphEdge
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.graph_step_field_reading import GraphStepFieldReading
from harness.include_alias_group import IncludeAliasGroup
from harness.step_dependency_graph_creating import StepDependencyGraphCreating
from harness.step_identity_resolving import StepIdentityResolving


"""
solid-name: StepDependencyGraphFactory
solid-category: service
solid-spec: [SPEC-027]
solid-description: Creates a typed dependency graph from workflow steps and include groups.
"""
class StepDependencyGraphFactory(StepDependencyGraphCreating):

    def __init__(
        self,
        identity_resolver: StepIdentityResolving,
        graph_factory: DirectedGraphCreating,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._identity_resolver = identity_resolver
        self._graph_factory = graph_factory
        self._error_factory = error_factory

    def create(
        self,
        steps: list[GraphStepFieldReading],
        alias_groups: list[IncludeAliasGroup],
    ) -> DirectedGraph:
        step_ids = [self._identity_resolver.resolve(step) for step in steps]
        node_ids = [*step_ids, *[group.alias for group in alias_groups]]
        edges = []
        for step, step_id in zip(steps, step_ids):
            for dependency in step.depends_on or []:
                if dependency not in node_ids:
                    raise self._error_factory.create(
                        f"Step '{step_id}' depends on unknown step '{dependency}'"
                    )
                edges.append(
                    DirectedGraphEdge(
                        source_id=dependency,
                        target_id=step_id,
                    )
                )
        return self._graph_factory.create(node_ids, edges)
