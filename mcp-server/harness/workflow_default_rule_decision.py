"""Represents rule enablement inherited from its workflow declaration."""

from typing import Literal

from harness.rule_enablement_decision import RuleEnablementDecision


"""
solid-name: WorkflowDefaultRuleDecision
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records effective review-rule enablement when no project override is authored.
"""
class WorkflowDefaultRuleDecision(RuleEnablementDecision):
    source: Literal["workflow_default"] = "workflow_default"
    effective: Literal[True] = True
