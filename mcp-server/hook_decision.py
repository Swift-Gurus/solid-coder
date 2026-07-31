"""
solid-name: HookDecision
solid-category: value-object
solid-description: Represents a hook handler's authorization decision with optional supporting information.
solid-tags: [hook]
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HookDecision:
    allow: bool = True
    reason: Optional[str] = None
    additional_context: Optional[str] = None
