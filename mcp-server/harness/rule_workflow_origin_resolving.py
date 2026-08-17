"""Defines ownership classification for an enrolled workflow source."""

from typing import Protocol

from harness.rule_workflow_origin import RuleWorkflowOrigin
from harness.workflow_source import WorkflowSource


"""
solid-name: RuleWorkflowOriginResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for classifying enrolled workflow ownership provenance.
"""
class RuleWorkflowOriginResolving(Protocol):
    def resolve(self, source: WorkflowSource) -> RuleWorkflowOrigin: ...
