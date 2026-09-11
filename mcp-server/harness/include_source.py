"""Defines one resolved source of an include or inline group entry."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.workflow_include_runtime import WorkflowIncludeRuntime
from harness.workflow_output_declaration import WorkflowOutputDeclaration


"""
solid-name: IncludeSource
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Represents one resolved reusable workflow entry selected for inclusion.
"""
@dataclass(frozen=True)
class IncludeSource:
    alias: str
    steps: list[dict]
    flow_path: str
    runtime: WorkflowIncludeRuntime = field(default_factory=WorkflowIncludeRuntime)
    identity: str | None = None
    label: str | None = None
    source_path: str | None = None
    workflow_id: str | None = None
    rule_workflow: IncludedRuleWorkflow | None = None
    outputs: list[WorkflowOutputDeclaration] = field(default_factory=list)
    propagates_policy: bool = False
