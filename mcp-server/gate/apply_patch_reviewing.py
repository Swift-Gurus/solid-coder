"""Defines atomic review of every applicable file in one patch."""

from typing import Protocol

from hook_decision import HookDecision


"""
solid-name: ApplyPatchReviewing
solid-category: abstraction
solid-description: Contract for reviewing all applicable file changes and returning one aggregated authorization decision.
solid-tags: [hook]
"""
class ApplyPatchReviewing(Protocol):
    def review(
        self,
        tool_input: dict,
        session_id: str,
        cwd: str,
    ) -> HookDecision: ...
