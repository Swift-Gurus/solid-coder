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
import subprocess
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
MCP_DIR = SERVER_DIR.parent
PLUGIN_ROOT = MCP_DIR.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"

FIND_SPEC_SCRIPT = SKILLS_ROOT / "find-spec" / "scripts" / "find-spec-query.py"
BUILD_SPEC_SCRIPT = SKILLS_ROOT / "build-spec" / "scripts" / "build-spec-query.py"

sys.path.insert(0, str(MCP_DIR))
from lib import parse_frontmatter
from protocol import MCPServer

server = MCPServer("solid-coder-specs", "1.0.0")

_CHUNK_SIZE = 40_000


def _maybe_chunk(content: str, prefix: str) -> str:
    if len(content) <= _CHUNK_SIZE:
        return content
    import tempfile, time
    ts = int(time.time())
    chunks = [content[i:i + _CHUNK_SIZE] for i in range(0, len(content), _CHUNK_SIZE)]
    paths = []
    for n, chunk in enumerate(chunks, 1):
        path = Path(tempfile.gettempdir()) / f"solid-coder-{prefix}-{ts}-{n}of{len(chunks)}.md"
        path.write_text(chunk, encoding="utf-8")
        paths.append(str(path))
    lines = [
        f"Content is large ({len(content):,} chars across {len(chunks)} chunks).",
        "Read each file below in order using the Read tool:",
        "",
    ] + [f"- {p}" for p in paths]
    return "\n".join(lines)


def _run(cmd: list) -> tuple[bool, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, result.stderr.strip() or result.stdout.strip()


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
    from pathlib import Path as _Path
    p = _Path(file_path)
    if not p.exists():
        return (f"File not found: {file_path}. "
                "The input must be a spec markdown file. Use `/build-spec` to create one.")
    if p.suffix != ".md":
        return (f"Not a markdown file: {file_path}. "
                "The input must be a spec .md file with YAML frontmatter.")
    try:
        out = json.dumps(parse_frontmatter.parse(file_path))
        ok = True
    except Exception as e:
        ok, out = False, str(e)
    if not ok:
        return (f"No YAML frontmatter found in {file_path}: {out}. "
                "Spec files must start with a --- frontmatter block. Use `/build-spec` to create one.")
    try:
        fm = json.loads(out)
    except json.JSONDecodeError:
        return f"Could not parse frontmatter JSON from {file_path}: {out}"
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
    if action in ("scan", "children", "ancestors", "next-number"):
        script = FIND_SPEC_SCRIPT
    else:
        script = BUILD_SPEC_SCRIPT
    ok, out = _run([sys.executable, str(script), action] + args)
    if not ok:
        return f"Error: {out}"
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


# ---------------------------------------------------------------------------
# Tool: load_spec_context
# ---------------------------------------------------------------------------

@server.tool(
    name="load_spec_context",
    description=(
        "Load the full ancestor chain for a spec as readable text. "
        "Pass either spec_number (e.g. 'SPEC-042') or file_path to a spec markdown file — "
        "if file_path is given the spec number is parsed from its frontmatter automatically. "
        "Pass blocked=true to also include blocked-by specs."
    ),
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
    if not spec_number and not file_path:
        return "Error: either spec_number or file_path is required."
    if file_path and not spec_number:
        try:
            out = json.dumps(parse_frontmatter.parse(file_path))
            ok = True
        except Exception as e:
            ok, out = False, str(e)
        if not ok:
            return f"Error parsing spec frontmatter: {out}"
        try:
            fm = json.loads(out)
            spec_number = fm.get("number")
            if not spec_number:
                return f"Error: no 'number' field found in frontmatter of {file_path}"
        except json.JSONDecodeError:
            return f"Error: could not parse frontmatter JSON from {file_path}"
    cmd = [sys.executable, str(FIND_SPEC_SCRIPT), "ancestors", spec_number]
    if blocked:
        cmd.append("--blocked")
    ok, out = _run(cmd)
    if not ok:
        return f"Error: {out}"

    try:
        specs = json.loads(out)
    except json.JSONDecodeError:
        return out

    if not specs:
        return f"No ancestors found for {spec_number}."

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

    return _maybe_chunk("\n".join(lines), f"spec-context-{spec_number}")


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
    ok, out = _run([sys.executable, str(BUILD_SPEC_SCRIPT), "update-status", spec_number, status])
    if not ok:
        return f"Error: {out}"
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


if __name__ == "__main__":
    server.run()
