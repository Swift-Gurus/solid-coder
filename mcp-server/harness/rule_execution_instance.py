"""Defines one materialized executable review-rule instance."""

from dataclasses import dataclass, field

from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.step_def import StepDef


"""
solid-name: RuleExecutionInstance
solid-category: model
solid-spec: [SPEC-039]
solid-description: Associates one rule workflow identity with its runtime instance ID and materialized executable steps.
"""
@dataclass(frozen=True)
class RuleExecutionInstance:
    workflow: IncludedRuleWorkflow
    instance_id: str
    steps: list[StepDef] = field(default_factory=list)
