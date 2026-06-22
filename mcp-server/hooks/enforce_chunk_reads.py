#!/usr/bin/env python3
"""PreToolUse hook — block non-Read tools while MCP chunk files are unread.

When the MCP docs server returns content too large for a single response, it
writes numbered chunk files prefixed with "solid-coder-" and tells the agent
to read each one with the Read tool.

The tracker hook (PostToolUse on MCP tools) registers which chunk files belong
to THIS session. This hook only blocks on registered-but-unread chunks, so
concurrent sessions never interfere with each other.

State file written by chunk_tracker.py.
"""

import json
import sys
import time
import tempfile
from pathlib import Path

_TTL_SECONDS = 1800


def _state_file(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"solid-coder-chunks-{session_id}.json"


def _pending_chunks(session_id: str) -> list:
    """Return registered chunk paths that have not been read and still exist."""
    sf = _state_file(session_id)
    try:
        state = json.loads(sf.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    registered = set(state.get("registered", []))
    read = set(state.get("read", []))
    pending = []
    for path in sorted(registered - read):
        p = Path(path)
        if not p.exists():
            continue
        # TTL: skip chunks whose timestamp is too old
        import re
        m = re.search(r"solid-coder-.+-(\d+)-\d+of\d+\.md$", path)
        if m and time.time() - int(m.group(1)) > _TTL_SECONDS:
            continue
        pending.append(path)
    return pending


def _allow() -> None:
    sys.exit(0)


def _block(pending: list) -> None:
    lines = [
        "[chunk-read-gate] You must read ALL pending MCP chunk files with the Read",
        "tool before using any other tool. Remaining chunks:",
        "",
    ] + [f"  - {p}" for p in pending] + [
        "",
        "Read each file above in order, then retry your action.",
    ]
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "\n".join(lines),
        }
    }))
    sys.stdout.flush()
    sys.exit(0)


def main() -> None:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        _allow()
        return

    if event.get("tool_name") == "Read":
        _allow()
        return

    session_id = event.get("session_id", "unknown")
    pending = _pending_chunks(session_id)
    if pending:
        _block(pending)
    else:
        _allow()


if __name__ == "__main__":
    main()
