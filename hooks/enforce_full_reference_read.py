#!/usr/bin/env python3
"""PreToolUse hook — block partial reads of files inside references/.

If a Read call targets a file under the references/ directory and specifies
an offset or limit, deny it so the agent always reads the full file.
"""
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
REFS_ROOT = PLUGIN_ROOT / "references"

try:
    event = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

if event.get("tool_name") != "Read":
    sys.exit(0)

tool_input = event.get("tool_input", {})
file_path = tool_input.get("file_path", "")

try:
    is_reference = Path(file_path).is_relative_to(REFS_ROOT)
except Exception:
    is_reference = str(REFS_ROOT) in file_path

if not is_reference:
    sys.exit(0)

has_offset = tool_input.get("offset") is not None
has_limit = tool_input.get("limit") is not None

if has_offset or has_limit:
    parts = []
    if has_offset:
        parts.append(f"offset={tool_input['offset']}")
    if has_limit:
        parts.append(f"limit={tool_input['limit']}")
    print(
        f"Partial read blocked for reference file: {file_path} "
        f"({', '.join(parts)}). Read the full file — reference files must be loaded completely.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
