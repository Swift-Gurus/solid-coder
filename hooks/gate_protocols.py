"""
solid-description: Canonical protocol definitions shared across the pre_write_gate pipeline.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Optional, Protocol

from hook_utils import GateHandling  # noqa: F401 — re-exported for consumers


class HealthChecking(Protocol):
    def check(self, content: str, path: str, language: str, parent_session_id: str) -> Optional[list]: ...


class ViolationFormatting(Protocol):
    def format_block_reason(self, violations: list) -> str: ...


class ContentSimulating(Protocol):
    def simulate(self, tool_name: str, tool_input: dict) -> tuple: ...


class FrontmatterFixing(Protocol):
    def fix(self, content: str, session_id: str, path: str) -> Optional[str]: ...


class HealthGateChecking(Protocol):
    def check(self, content: str, path: str, language: str, session_id: str, gate: GateHandling, file_name: str) -> bool: ...


class FrontmatterGateApplying(Protocol):
    def apply(self, content: str, session_id: str, path: str, gate: GateHandling, file_name: str) -> Optional[str]: ...
