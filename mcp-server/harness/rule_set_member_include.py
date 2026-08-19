"""Defines one generated member of an explicit rule-set include."""

from __future__ import annotations

from dataclasses import dataclass

from harness.condition_declaration import ConditionDeclaration
from harness.workflow_include_runtime import WorkflowIncludeRuntime


"""
solid-name: RuleSetMemberInclude
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries one catalog rule workflow and the runtime controls applied by its rule-set boundary.
"""
@dataclass(frozen=True)
class RuleSetMemberInclude:
    workflow_id: str
    alias: str
    runtime: WorkflowIncludeRuntime
    condition: ConditionDeclaration | None = None
