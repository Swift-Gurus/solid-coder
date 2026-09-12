"""Classifies enrolled workflow ownership from the active project boundary."""

from harness.project_context import ProjectDirectoryReading
from harness.rule_workflow_origin import RuleWorkflowOrigin
from harness.rule_workflow_origin_resolving import RuleWorkflowOriginResolving
from harness.workflow_source import WorkflowSource


"""
solid-name: RuleWorkflowOriginResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Classifies enrolled workflow ownership against the resolved active-project boundary.
"""
class RuleWorkflowOriginResolver(RuleWorkflowOriginResolving):

    def __init__(self, project_directory: ProjectDirectoryReading) -> None:
        self._project_directory = project_directory

    def resolve(self, source: WorkflowSource) -> RuleWorkflowOrigin:
        try:
            source.entry_path.resolve().relative_to(
                self._project_directory.read().resolve()
            )
            return RuleWorkflowOrigin.PROJECT
        except ValueError:
            return RuleWorkflowOrigin.PLUGIN
