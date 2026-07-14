"""
solid-description: Contract for applying a gate against content.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Optional, Protocol

from hook_utils import GateHandling


class FrontmatterGateApplying(Protocol):
    def apply(self, content: str, session_id: str, path: str, gate: GateHandling, file_name: str) -> Optional[str]: ...