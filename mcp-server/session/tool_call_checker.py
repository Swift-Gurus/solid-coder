"""
solid-description: Validates that required tools were invoked for a given session type.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Protocol

_HOOKS_DIR = Path(__file__).resolve().parents[1]
_SESSION_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _SESSION_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from mcp_tool_call_reader import McpToolCallReading

_DEFAULT_REQUIRED: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "health_check": frozenset({"submit_batch_findings"}),
        "review": frozenset({"submit_batch_findings"}),
    }
)


class RequiredToolsProviding(Protocol):
    def required_for(self, session_type: str) -> frozenset[str]: ...


class DefaultRequiredTools:
    """Returns the required MCP tool names for each managed session type."""

    def __init__(
        self, mapping: Mapping[str, frozenset[str]] = _DEFAULT_REQUIRED
    ) -> None:
        self._mapping = mapping

    def required_for(self, session_type: str) -> frozenset[str]:
        return self._mapping.get(session_type, frozenset())


class ToolCallChecker:
    """Validates that required MCP tools were called for the given session type."""

    def __init__(
        self,
        reader: McpToolCallReading,
        required_tools: RequiredToolsProviding,
    ) -> None:
        self._reader = reader
        self._required_tools = required_tools

    def check(self, transcript_path: str | None, session_type: str) -> dict:
        required = self._required_tools.required_for(session_type)
        if not required:
            return {"allow": True}
        called = self._reader.read(transcript_path) if transcript_path else set()
        missing = required - called
        if not missing:
            return {"allow": True}
        tools_str = ", ".join(f"mcp__pipeline__{t}" for t in sorted(missing))
        return {
            "allow": False,
            "reason": (
                f"Required tool(s) not called: {tools_str}. "
                f"You MUST call {tools_str} — do not write findings as text or use file tools."
            ),
        }
