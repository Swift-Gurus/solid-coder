#!/usr/bin/env python3
"""PostToolUse hook — register and track MCP chunk file reads.

Two responsibilities, both using the same state file:

  1. MCP tool PostToolUse: scan the tool response for solid-coder chunk paths
     and register them for this session. This is how the enforcement hook knows
     which chunks belong to THIS session (not another concurrent session).

  2. Read tool PostToolUse: when a chunk file is read, mark it as consumed so
     the enforcement hook knows it no longer needs to be read.

State file: {tmpdir}/solid-coder-chunks-{session_id}.json
Schema: {"registered": [...paths...], "read": [...paths...]}
"""

import json
import re
import sys
import tempfile
from pathlib import Path

_CHUNK_MARKER = "solid-coder-"
_CHUNK_PATH_RE = re.compile(r"(/\S+/solid-coder-[^\s]+\.md)")


def _state_file(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"solid-coder-chunks-{session_id}.json"


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"registered": [], "read": []}


def _save(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _prune(state: dict) -> dict:
    """Remove entries for chunk files that no longer exist on disk."""
    existing = lambda paths: [p for p in paths if Path(p).exists()]
    state["registered"] = existing(state.get("registered", []))
    state["read"] = existing(state.get("read", []))
    return state


def _extract_chunk_paths(response) -> list:
    """Extract solid-coder chunk paths from any shape of tool_response."""
    text = response if isinstance(response, str) else json.dumps(response)
    return _CHUNK_PATH_RE.findall(text)


def main() -> None:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    session_id = event.get("session_id", "unknown")
    sf = _state_file(session_id)

    if tool_name.startswith("mcp__"):
        # Register any chunk paths returned in this tool's response
        response = event.get("tool_response", "")
        paths = _extract_chunk_paths(response)
        if not paths:
            sys.exit(0)
        state = _prune(_load(sf))
        registered = set(state["registered"]) | set(paths)
        state["registered"] = list(registered)
        _save(sf, state)

    elif tool_name == "Read":
        # Mark a chunk as consumed when Read succeeds
        file_path = (event.get("tool_input") or {}).get("file_path", "")
        if _CHUNK_MARKER not in file_path or not file_path.endswith(".md"):
            sys.exit(0)
        state = _prune(_load(sf))
        read_set = set(state["read"]) | {file_path}
        state["read"] = list(read_set)
        _save(sf, state)

    sys.exit(0)


if __name__ == "__main__":
    main()
