"""
solid-description: Contract that defines checking content against validation rules.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol

from hook_utils import GateHandling


class HealthGateChecking(Protocol):
    def check(self, content: str, path: str, language: str, session_id: str, gate: GateHandling, file_name: str, cwd: str = "") -> bool: ...