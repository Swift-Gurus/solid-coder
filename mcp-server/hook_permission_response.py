from dataclasses import dataclass

from hook_decision import HookDecision


"""
solid-name: HookPermissionResponse
solid-category: model
solid-description: Carries a hook permission decision and optional corrected tool input for the response boundary.
"""
@dataclass(frozen=True)
class HookPermissionResponse:
    decision: HookDecision
    updated_input: dict | None = None
