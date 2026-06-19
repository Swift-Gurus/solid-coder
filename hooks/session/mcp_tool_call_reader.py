"""
solid-description: Identifies tools invoked in session transcripts.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
from typing import Protocol

_HOOKS_DIR = Path(__file__).resolve().parents[1]
_SESSION_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _SESSION_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from slack_notify import JSONLTranscriptParser, JSONLParsing, FileSystemLineReader  # noqa: E402
from hook_utils import ensure_on_path  # noqa: E402 -- re-export for callers

ensure_on_path(_HOOKS_DIR)


class McpToolCallReading(Protocol):
    def read(self, transcript_path: str) -> set: ...


class McpToolCallReader:
    """Reads MCP tool short-names from a session transcript.

    Handles three formats:
    - Claude Code: assistant/tool_use events
    - Codex --json stream: item.completed/mcp_tool_call events
    - Codex saved session (rollout): response_item/function_call events
    """

    def __init__(self, parser: JSONLParsing) -> None:
        self._parser = parser

    def read(self, transcript_path: str) -> set:
        """Return short tool names called in the transcript."""
        called: set = set()
        for event in self._parser.messages(transcript_path):
            self._collect_claude(called, event)
            self._collect_codex_json(called, event)
            self._collect_codex_rollout(called, event)
        return called

    def _collect_claude(self, called: set, event: dict) -> None:
        if event.get("type") != "assistant":
            return
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                self._add(called, block.get("name", ""))

    def _collect_codex_json(self, called: set, event: dict) -> None:
        """Codex --json event stream: item.completed with mcp_tool_call item."""
        item = event.get("item", {})
        if item.get("type") == "mcp_tool_call":
            called.add(item.get("tool", ""))

    def _collect_codex_rollout(self, called: set, event: dict) -> None:
        """Codex saved session (rollout) format: response_item with function_call payload."""
        if event.get("type") != "response_item":
            return
        payload = event.get("payload", {})
        if payload.get("type") == "function_call":
            self._add(called, payload.get("name", ""))

    def _add(self, called: set, full_name: str) -> None:
        """Add tool short name, stripping any mcp__*__ or mcp__*_ prefix."""
        parts = full_name.split("__")
        called.add(parts[-1] if len(parts) >= 2 else full_name)


def make_mcp_tool_call_reader() -> McpToolCallReader:
    """Factory: returns a McpToolCallReader with production defaults."""
    return McpToolCallReader(parser=JSONLTranscriptParser(file_reader=FileSystemLineReader()))
