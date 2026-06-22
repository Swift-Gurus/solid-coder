"""
solid-description: Validates that required tools were invoked for a given session type.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parents[1]
_SESSION_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _SESSION_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from mcp_tool_call_reader import McpToolCallReading  # noqa: E402

_DEFAULT_REQUIRED: dict = {
    "health_check": {"submit_batch_findings"},
    "review": {"submit_batch_findings"},
}


class RequiredToolsProviding(Protocol):
    def required_for(self, session_type: str) -> set: ...


class DefaultRequiredTools:
    """Returns the required MCP tool names for each managed session type."""

    def __init__(self, mapping: dict = _DEFAULT_REQUIRED) -> None:
        self._mapping = mapping

    def required_for(self, session_type: str) -> set:
        return self._mapping.get(session_type, set())


class ToolCallChecker:
    """Validates that required MCP tools were called for the given session type."""

    def __init__(
        self,
        reader: McpToolCallReading,
        required_tools: RequiredToolsProviding = DefaultRequiredTools(),
    ) -> None:
        self._reader = reader
        self._required_tools = required_tools

    def check(self, transcript_path: Optional[str], session_type: str) -> dict:
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