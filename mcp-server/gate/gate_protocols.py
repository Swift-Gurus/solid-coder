"""
solid-description: Canonical protocol definitions for gate operations.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Optional, Protocol

from hook_utils import GateHandling  # noqa: F401 — re-exported for consumers
from guard_checking import GuardChecking  # noqa: F401 — re-exported for consumers
from exclusion_checking import ExclusionChecking  # noqa: F401 — re-exported for consumers
from extension_lookup import ExtensionLookup  # noqa: F401 — re-exported for consumers
from coordinator_running import CoordinatorRunning  # noqa: F401 — re-exported for consumers
from coordinator_making import CoordinatorMaking  # noqa: F401 — re-exported for consumers
from health.hc_checker import HealthChecking  # noqa: F401 — re-exported for consumers; canonical definition
from health.hc_violation_parser import BlockReasonFormatting as ViolationFormatting  # noqa: F401 — re-exported; canonical definition


class ContentSimulating(Protocol):
    def simulate(self, tool_name: str, tool_input: dict) -> tuple: ...


class FrontmatterFixing(Protocol):
    def fix(self, content: str, session_id: str, path: str) -> Optional[str]: ...


class HealthGateChecking(Protocol):
    def check(self, content: str, path: str, language: str, session_id: str, gate: GateHandling, file_name: str, cwd: str = "") -> bool: ...


class FrontmatterGateApplying(Protocol):
    def apply(self, content: str, session_id: str, path: str, gate: GateHandling, file_name: str) -> Optional[str]: ...
