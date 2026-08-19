"""Defines one enrolled rule in an effective review plan."""

from pathlib import Path
from typing import Union

from pydantic import BaseModel, ConfigDict, Field

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.project_policy_rule_decision import ProjectPolicyRuleDecision
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_workflow_origin import RuleWorkflowOrigin
from harness.workflow_default_rule_decision import WorkflowDefaultRuleDecision


"""
solid-name: EffectiveRulePlanEntry
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records stable workflow provenance, applicability metadata, hashing, and enablement for one review rule.
"""
class EffectiveRulePlanEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    workflow_id: str
    origin: RuleWorkflowOrigin
    source_path: Path
    workflow_hash: str
    category: str = ""
    match: RuleMatchDeclaration = Field(default_factory=RuleMatchDeclaration)
    enablement: Union[
        WorkflowDefaultRuleDecision,
        ProjectPolicyRuleDecision,
    ]
    metrics: list[EffectiveMetricPlanEntry] = Field(default_factory=list)
