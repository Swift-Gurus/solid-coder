"""
solid-name: HookDecision
solid-category: value-object
solid-description: Represents a hook handler's authorization decision with optional supporting information.
solid-tags: [hook]
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HookDecision:
    allow: bool = True
    reason: str | None = None
    additional_context: str | None = None
