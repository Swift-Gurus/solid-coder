"""Creates combined rule-presentation identities."""

from harness.combined_rule_presentation import CombinedRulePresentation
from harness.combined_rule_presentation_creating import (
    CombinedRulePresentationCreating,
)


"""
solid-name: CombinedRulePresentationFactory
solid-category: factory
solid-spec: [SPEC-043, SPEC-045]
solid-description: Creates immutable combined presentation identity values.
"""
class CombinedRulePresentationFactory(CombinedRulePresentationCreating):
    def create(
        self,
        group_alias: str,
        workflow_alias: str,
    ) -> CombinedRulePresentation:
        return CombinedRulePresentation(
            group_alias=group_alias,
            rule_alias=workflow_alias,
        )
