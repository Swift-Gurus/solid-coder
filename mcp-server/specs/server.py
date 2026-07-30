#!/usr/bin/env python3
"""solid-coder specs MCP server — spec file operations for subagents.

Tools:
  parse_spec        — parse YAML frontmatter from a spec file
  query_specs       — navigate spec hierarchy (scan, children, ancestors, next-number)
  load_spec_context — load full ancestor chain content as readable text
  update_spec_status — update spec status and propagate up hierarchy

No external dependencies. Python 3.9+.
"""

import json
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
MCP_DIR = SERVER_DIR.parent
PLUGIN_ROOT = MCP_DIR.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"

FIND_SPEC_SCRIPT = SKILLS_ROOT / "find-spec" / "scripts" / "find-spec-query.py"
BUILD_SPEC_SCRIPT = SKILLS_ROOT / "build-spec" / "scripts" / "build-spec-query.py"

sys.path.insert(0, str(MCP_DIR))
from spec import parse_frontmatter
from hook_utils import SubprocessAdapter, SubprocessError, SubprocessJsonRunner
from mcp_server_factory import MCPServerFactory

server = MCPServerFactory().build("solid-coder-specs", "1.0.0")

_json_runner = SubprocessJsonRunner(SubprocessAdapter())


def _run_json_tool(cmd: list):
    """Run cmd and parse JSON stdout. Returns (ok, result_or_error_message)."""
    try:
        return True, _json_runner.run(cmd)
    except SubprocessError as e:
        return False, f"Error: {e}"


def _parse_frontmatter_or_error(file_path):
    try:
        return parse_frontmatter.parse(file_path), None
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# Tool: parse_spec
# ---------------------------------------------------------------------------

@server.tool(
    name="parse_spec",
    description=(
        "Parse YAML frontmatter from a spec file. "
        "Returns JSON with all frontmatter fields including number, type, status, parent, blocked-by."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the spec markdown file.",
            },
        },
        "required": ["file_path"],
    },
)
def parse_spec(file_path):
    p = Path(file_path)
    if not p.exists():
        return (f"File not found: {file_path}. "
                "The input must be a spec markdown file. Use `/build-spec` to create one.")
    if p.suffix != ".md":
        return (f"Not a markdown file: {file_path}. "
                "The input must be a spec .md file with YAML frontmatter.")
    fm, err = _parse_frontmatter_or_error(file_path)
    if err is not None:
        return (f"No YAML frontmatter found in {file_path}: {err}. "
                "Spec files must start with a --- frontmatter block. Use `/build-spec` to create one.")
    if "number" not in fm:
        return (f"Frontmatter in {file_path} is missing the required `number` field. "
                "Use `/build-spec` to generate a properly structured spec.")
    return fm


# ---------------------------------------------------------------------------
# Tool: query_specs
# ---------------------------------------------------------------------------

@server.tool(
    name="query_specs",
    description=(
        "Navigate the spec hierarchy. "
        "Actions: scan, children, ancestors, next-number, types, statuses, resolve-path."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["scan", "children", "ancestors", "next-number", "types", "statuses", "resolve-path"],
                "description": "Which query to run.",
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Arguments for the action (e.g. ['SPEC-042'] for children/ancestors, or filter flags for scan).",
            },
        },
        "required": ["action"],
    },
)
def query_specs(action, args=None):
    args = args or []
    script = FIND_SPEC_SCRIPT if action in ("scan", "children", "ancestors", "next-number") else BUILD_SPEC_SCRIPT
    _, result = _run_json_tool([sys.executable, str(script), action] + args)
    return result


# ---------------------------------------------------------------------------
# Tool: load_spec_context
# ---------------------------------------------------------------------------

def _resolve_spec_number(spec_number, file_path):
    """Returns (spec_number, error_message)."""
    if not spec_number and not file_path:
        return None, "Error: either spec_number or file_path is required."
    if file_path and not spec_number:
        fm, err = _parse_frontmatter_or_error(file_path)
        if err is not None:
            return None, f"Error parsing spec frontmatter: {err}"
        spec_number = fm.get("number")
        if not spec_number:
            return None, f"Error: no 'number' field found in frontmatter of {file_path}"
    return spec_number, None


def _load_ancestors(spec_number, blocked):
    """Returns (specs_list, error_message)."""
    cmd = [sys.executable, str(FIND_SPEC_SCRIPT), "ancestors", spec_number]
    if blocked:
        cmd.append("--blocked")
    ok, result = _run_json_tool(cmd)
    return (result, None) if ok else (None, result)


def _format_spec_context(spec_number, specs):
    sep = "=" * 60
    lines = [sep, f"  SPEC CONTEXT: {spec_number} ({len(specs)} specs)", sep]
    for s in specs:
        number = s.get("number", "?")
        feature = s.get("feature", "")
        status = s.get("status", "")
        path = s.get("path", "")
        lines.append(f"\n--- {number} — {feature} [{status}] ---\n")
        if path:
            try:
                lines.append(Path(path).read_text(encoding="utf-8").strip())
            except OSError as e:
                lines.append(f"(Could not read: {e})")
        lines.append("")
    lines.append(sep)
    return "\n".join(lines)


@server.tool(
    name="load_spec_context",
    description=(
        "Load the full ancestor chain for a spec as readable text. "
        "Pass either spec_number (e.g. 'SPEC-042') or file_path to a spec markdown file — "
        "if file_path is given the spec number is parsed from its frontmatter automatically. "
        "Pass blocked=true to also include blocked-by specs."
    ),
    meta={"anthropic/maxResultSizeChars": 1000000},
    input_schema={
        "type": "object",
        "properties": {
            "spec_number": {
                "type": "string",
                "description": "Spec number, e.g. 'SPEC-042'. Either this or file_path is required.",
            },
            "file_path": {
                "type": "string",
                "description": "Absolute path to a spec markdown file. Spec number is parsed from its frontmatter.",
            },
            "blocked": {
                "type": "boolean",
                "description": "Also include blocked-by specs.",
            },
        },
    },
)
def load_spec_context(spec_number=None, file_path=None, blocked=False):
    spec_number, err = _resolve_spec_number(spec_number, file_path)
    if err is not None:
        return err
    specs, err = _load_ancestors(spec_number, blocked)
    if err is not None:
        return err
    if not specs:
        return f"No ancestors found for {spec_number}."
    return _format_spec_context(spec_number, specs)


# ---------------------------------------------------------------------------
# Tool: update_spec_status
# ---------------------------------------------------------------------------

@server.tool(
    name="update_spec_status",
    description=(
        "Update a spec's status and propagate changes up the hierarchy. "
        "Valid statuses: draft, ready, in-progress, done, blocked."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "spec_number": {
                "type": "string",
                "description": "Spec number, e.g. 'SPEC-042'.",
            },
            "status": {
                "type": "string",
                "description": "New status value.",
            },
        },
        "required": ["spec_number", "status"],
    },
)
def update_spec_status(spec_number, status):
    _, result = _run_json_tool([sys.executable, str(BUILD_SPEC_SCRIPT), "update-status", spec_number, status])
    return result


if __name__ == "__main__":
    server.run()
