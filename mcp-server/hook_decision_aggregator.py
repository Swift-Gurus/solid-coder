"""
solid-name: HookDecisionAggregator
solid-category: service
solid-description: Aggregates multiple hook decisions with a denial-wins rule.
solid-tags: [hook]
"""

from typing import List

from hook_decision import HookDecision


class HookDecisionAggregator:
    def aggregate(self, decisions: List[HookDecision]) -> HookDecision:
        denials = [d for d in decisions if not d.allow]
        contexts = [d.additional_context for d in decisions if d.additional_context]
        merged_context = "\n".join(contexts) or None
        if denials:
            reasons = [d.reason for d in denials if d.reason]
            return HookDecision(allow=False, reason="\n".join(reasons) or None, additional_context=merged_context)
        return HookDecision(allow=True, additional_context=merged_context)