"""Coordinates recursive expansion of workflow includes and inline groups."""

from __future__ import annotations

from harness.include_resolution import IncludeResolution
from harness.include_resolving import IncludeResolving
from harness.include_traversal_context import IncludeTraversalContext
from harness.include_traversing import IncludeTraversing
from harness.path_canonicalizing import PathCanonicalizing
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_include_runtime import WorkflowIncludeRuntime
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: IncludeResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Coordinates recursive expansion of workflow includes and inline groups.
"""
class IncludeResolver(IncludeResolving):

    def __init__(
        self,
        path_canonicalizer: PathCanonicalizing,
        traverser: IncludeTraversing,
    ) -> None:
        self._path_canonicalizer = path_canonicalizer
        self._traverser = traverser

    def resolve(
        self,
        raw_steps: list[dict],
        flow_file_path: str,
        search_paths: list[str] | None = None,
        root_workflow_id: str | None = None,
        execution: WorkflowExecutionMode = WorkflowExecutionMode.GRANULAR,
        presentation: WorkflowPresentationMode = WorkflowPresentationMode.INDIVIDUAL,
    ) -> IncludeResolution:
        root_path = self._path_canonicalizer.canonicalize(flow_file_path)
        return self._traverser.traverse(
            raw_steps,
            search_paths or [],
            IncludeTraversalContext(
                flow_file_path=flow_file_path,
                ancestor_identities=[root_path],
                ancestor_labels=[root_workflow_id or root_path],
                runtime=WorkflowIncludeRuntime(
                    execution=execution,
                    presentation=presentation,
                ),
            ),
        )
