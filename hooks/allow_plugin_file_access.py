#!/usr/bin/env python3
"""PermissionRequest hook — auto-allow Read/Write/Edit for plugin-owned paths.

Auto-approves:
  - Any file inside ${CLAUDE_PLUGIN_ROOT}                      (plugin source)
  - Any file inside ${CLAUDE_PROJECT_DIR}/.solid_coder/        (plugin output)
  - Any file inside ${CLAUDE_PROJECT_DIR}/.claude/specs/       (project specs, nested)
  - Any file inside ${CLAUDE_PROJECT_DIR}/specs/               (project specs, root-level)
"""
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parents[1]))

project_dir_env = os.environ.get("CLAUDE_PROJECT_DIR")
PROJECT_DIR = Path(project_dir_env) if project_dir_env else None

try:
    event = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool_input = event.get("tool_input", {})
file_path = tool_input.get("file_path") or tool_input.get("path", "")

if not file_path:
    sys.exit(0)

target = Path(file_path)

def is_relative_to_safe(path, base):
    try:
        return path.is_relative_to(base)
    except Exception:
        return str(base) in str(path)

is_plugin_file = is_relative_to_safe(target, PLUGIN_ROOT)

is_output_file = (
    PROJECT_DIR is not None
    and is_relative_to_safe(target, PROJECT_DIR / ".solid_coder")
)

is_spec_file = PROJECT_DIR is not None and (
    is_relative_to_safe(target, PROJECT_DIR / ".claude" / "specs")
    or is_relative_to_safe(target, PROJECT_DIR / "specs")
)

behavior = "allow" if (is_plugin_file or is_output_file or is_spec_file) else "ask"
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {"behavior": behavior},
    }
}))
sys.exit(0)
