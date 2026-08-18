"""Defines one enrolled rule source paired with its resolved executable workflow."""

from dataclasses import dataclass

from harness.flow_def import FlowDef
from harness.workflow_source import WorkflowSource


"""
solid-name: ResolvedRuleWorkflow
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries one enrolled workflow source and its fully resolved typed executable definition.
"""
@dataclass(frozen=True)
class ResolvedRuleWorkflow:
    source: WorkflowSource
    workflow: FlowDef
