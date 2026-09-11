"""Defines combined rule-presentation construction."""

from typing import Protocol

from harness.combined_rule_presentation import CombinedRulePresentation


"""
solid-name: CombinedRulePresentationCreating
solid-category: abstraction
solid-spec: [SPEC-043, SPEC-045]
solid-description: Contract for creating combined presentation identity for a nested workflow.
"""
class CombinedRulePresentationCreating(Protocol):
    def create(
        self,
        group_alias: str,
        workflow_alias: str,
    ) -> CombinedRulePresentation: ...
