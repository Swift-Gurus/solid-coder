"""Prepares traversal context for nested include sources."""

from harness.include_cycle_guarding import IncludeCycleGuarding
from harness.include_source import IncludeSource
from harness.include_source_expansion_preparing import IncludeSourceExpansionPreparing
from harness.include_traversal_context import IncludeTraversalContext
from harness.workflow_include_policy_resolver import (
    WorkflowIncludePolicyResolver,
    WorkflowIncludePolicyResolving,
)

_DEFAULT_POLICY: WorkflowIncludePolicyResolving = WorkflowIncludePolicyResolver()


"""
solid-name: IncludeSourceExpansionPreparer
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Validates and prepares traversal context for a nested include source.
"""


class IncludeSourceExpansionPreparer(IncludeSourceExpansionPreparing):
    def __init__(
        self,
        cycle_guard: IncludeCycleGuarding,
        policy: WorkflowIncludePolicyResolving = _DEFAULT_POLICY,
    ) -> None:
        self._cycle_guard = cycle_guard
        self._policy = policy

    def prepare(
        self,
        source: IncludeSource,
        parent: IncludeTraversalContext,
    ) -> IncludeTraversalContext:
        self._cycle_guard.check(
            source.identity,
            source.label,
            parent.ancestor_identities,
            parent.ancestor_labels,
        )
        identities = parent.ancestor_identities + (
            [source.identity] if source.identity else []
        )
        labels = parent.ancestor_labels + ([source.label] if source.label else [])
        return IncludeTraversalContext(
            flow_file_path=source.flow_path,
            ancestor_identities=identities,
            ancestor_labels=labels,
            runtime=self._policy.resolve(source.runtime, parent.runtime),
        )
