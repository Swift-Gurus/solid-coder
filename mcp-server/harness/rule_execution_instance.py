"""Defines one materialized executable review-rule instance."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.rule_review_provenance import RuleReviewProvenance
from harness.step_def import StepDef


"""
solid-name: RuleExecutionInstance
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records the provenance and execution scope of one materialized review rule.
"""
@dataclass(frozen=True)
class RuleExecutionInstance:
    workflow: IncludedRuleWorkflow
    instance_id: str
    provenance: RuleReviewProvenance
    steps: list[StepDef] = field(default_factory=list)
