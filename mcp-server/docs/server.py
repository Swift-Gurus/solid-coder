#!/usr/bin/env python3
"""solid-coder docs MCP server — loads principle documentation on demand.

Returns file content directly (frontmatter stripped) instead of paths.
Supports mode-aware section filtering, tag-based principle filtering, and
on-demand example loading.

Tools:
  load_rules         — load principle docs for a pipeline mode
  load_examples      — load examples for a specific principle
  load_pattern       — load a design pattern by name
  get_candidate_tags — list all available activation tags

No external dependencies. Python 3.9+.
"""

import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
MCP_DIR = SERVER_DIR.parent
PLUGIN_ROOT = MCP_DIR.parent
REFS_ROOT = PLUGIN_ROOT / "references"
PATTERNS_ROOT = REFS_ROOT / "design_patterns"
SKILLS_ROOT = PLUGIN_ROOT / "skills"

sys.path.insert(0, str(MCP_DIR))

from lib import discover_principles, parse_frontmatter
import modes as modes_module
from protocol import MCPServer

server = MCPServer("solid-coder-docs", "1.0.0")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return content
    end = content.find("---", 3)
    if end == -1:
        return content
    body_start = end + 3
    if body_start < len(content) and content[body_start] == "\n":
        body_start += 1
    return content[body_start:]


def _read(path) -> str:
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")
        return _strip_frontmatter(raw)
    except OSError as e:
        return f"[could not read {path}: {e}]"


def _rel_label(path: Path) -> str:
    try:
        return str(path.relative_to(PLUGIN_ROOT))
    except ValueError:
        return path.name


def _collect_files(folder: Path, rule_path: str, exclude: set, profile: str) -> list:
    files = []
    if "rule" not in exclude:
        files.append(rule_path)
    if "instructions" not in exclude:
        instr_dir = "review" if profile == "review" else "fix"
        instr = folder / instr_dir / "instructions.md"
        if instr.is_file():
            files.append(str(instr))
    if "code_rules" not in exclude and profile == "code":
        code_instr = folder / "code" / "instructions.md"
        if code_instr.is_file():
            files.append(str(code_instr))
    if "examples" not in exclude:
        ex_dir = folder / "Examples"
        if ex_dir.is_dir():
            for f in sorted(ex_dir.iterdir()):
                if f.is_file():
                    files.append(str(f))
    if "patterns" not in exclude:
        try:
            fm = parse_frontmatter.parse(rule_path)
            for pp in (fm.get("required_patterns") or []):
                if isinstance(pp, str) and Path(pp).is_file():
                    files.append(pp)
        except Exception:
            pass
    return files


_STRIP_HEADINGS = frozenset({"severity bands", "quantitative metrics summary"})


def _strip_review_only_sections(content: str) -> str:
    """Remove sections only relevant to review agents (severity thresholds).

    Strips any heading whose normalised text is in _STRIP_HEADINGS plus all
    content until the next `---` horizontal rule (which acts as the section
    terminator in rule.md files).  Non-review modes need the violation
    definitions and exceptions — not the COMPLIANT/MINOR/SEVERE thresholds.
    """
    lines = content.splitlines(keepends=True)
    result = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            heading_text = stripped.lstrip("#").strip().rstrip(":").lower()
            if heading_text in _STRIP_HEADINGS:
                skipping = True
                continue
            skipping = False
        if skipping:
            if stripped == "---":
                skipping = False  # consume the separator, stop skipping
            continue
        result.append(line)
    return "".join(result)


def _render_principle(name: str, files: list, review_mode: bool) -> str:
    parts = [f"# {name}\n"]
    for p in files:
        label = _rel_label(Path(p))
        content = _read(p)
        if Path(p).name == "rule.md" and not review_mode:
            content = _strip_review_only_sections(content)
        parts.append(f"## {label}\n\n{content.rstrip()}\n")
    return "\n".join(parts)


_CHUNK_SIZE = 40_000


def _maybe_chunk(content: str, prefix: str) -> str:
    """Return content directly if small enough, otherwise save to chunk files.

    If content exceeds _CHUNK_SIZE, writes numbered files to /tmp and returns
    instructions for the agent to read them with the Read tool.
    """
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


def _all_principles() -> list:
    result = discover_principles.discover_and_filter(str(REFS_ROOT))
    return result["active_principles"] + result.get("skipped_principles", [])


# ---------------------------------------------------------------------------
# Tool: discover_principles
# ---------------------------------------------------------------------------

@server.tool(
    name="discover_principles",
    description=(
        "Discover active principles. Pass matched_tags to filter conditional principles "
        "to those relevant for the project's tech stack. Pass profile to restrict to "
        "principles that support a specific pipeline profile (code or review)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "matched_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags matched from the project. Conditional principles are only active if they share a tag.",
            },
            "profile": {
                "type": "string",
                "enum": ["code", "review"],
                "description": "Filter to principles supporting this profile.",
            },
        },
    },
)
def discover_principles_tool(matched_tags=None, profile=None):
    result = discover_principles.discover_and_filter(
        str(REFS_ROOT), matched_tags=matched_tags, profile=profile,
    )
    return {
        "active_principles": result["active_principles"],
        "skipped_principles": result.get("skipped_principles", []),
        "all_candidate_tags": result["all_candidate_tags"],
    }


# ---------------------------------------------------------------------------
# Tool: get_candidate_tags
# ---------------------------------------------------------------------------

@server.tool(
    name="get_candidate_tags",
    description=(
        "Return all activation tags from all principles. "
        "Match these against the project's imports/patterns to decide which "
        "conditional principles are active."
    ),
    input_schema={"type": "object", "properties": {}, "required": []},
)
def get_candidate_tags():
    result = discover_principles.discover_and_filter(str(REFS_ROOT))
    return {"candidate_tags": result["all_candidate_tags"]}


# ---------------------------------------------------------------------------
# Tool: load_rules
# ---------------------------------------------------------------------------

@server.tool(
    name="load_rules",
    description=(
        "Load principle documentation for a pipeline mode. "
        "Returns content with frontmatter stripped, concatenated per principle. "
        "Modes: code, review, planner, synth-impl, synth-fixes. "
        "Use matched_tags to skip conditional principles not relevant to the project. "
        "Use principle to load a single principle (required for review mode)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": list(modes_module.MODES.keys()),
                "description": "Pipeline mode — determines which sections of each principle to load.",
            },
            "matched_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags matched from the project. Filters out conditional principles with no matching tag.",
            },
            "principle": {
                "type": "string",
                "description": "Load only this principle (e.g. 'SRP'). Omit to load all active principles.",
            },
        },
        "required": ["mode"],
    },
)
def load_rules(mode, matched_tags=None, principle=None):
    try:
        cfg = modes_module.resolve(mode)
    except KeyError as e:
        return f"Error: {e}"

    profile = cfg["profile"]
    exclude = set(cfg.get("exclude", []))

    result = discover_principles.discover_and_filter(
        str(REFS_ROOT), matched_tags=matched_tags, profile=profile,
    )
    active = result["active_principles"]

    if principle:
        active = [p for p in active if p["name"].lower() == principle.lower()]
        if not active:
            valid = ", ".join(p["name"] for p in result["active_principles"])
            return f"Principle '{principle}' not found or not active for mode '{mode}'. Active: {valid}"

    blocks = []
    for p in active:
        files = _collect_files(
            folder=Path(p["folder"]),
            rule_path=p["rule_path"],
            exclude=exclude,
            profile=profile,
        )
        if files:
            blocks.append(_render_principle(p["name"], files, review_mode=mode == "review"))

    content = "\n\n---\n\n".join(blocks) if blocks else "No active principles found."
    return _maybe_chunk(content, f"rules-{mode}")


# ---------------------------------------------------------------------------
# Tool: load_examples
# ---------------------------------------------------------------------------

@server.tool(
    name="load_examples",
    description=(
        "Load all example files (compliant + violation Swift files) for a specific principle. "
        "Use during review to see concrete before/after patterns."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "principle": {
                "type": "string",
                "description": "Principle name, e.g. 'SRP', 'OCP', 'LSP', 'ISP', 'DRY'.",
            },
        },
        "required": ["principle"],
    },
)
def load_examples(principle):
    all_p = _all_principles()
    match = next((p for p in all_p if p["name"].lower() == principle.lower()), None)
    if not match:
        available = ", ".join(p["name"] for p in all_p)
        return f"Principle '{principle}' not found. Available: {available}"

    ex_dir = Path(match["folder"]) / "Examples"
    if not ex_dir.is_dir():
        return f"No Examples/ directory for principle '{principle}'."

    parts = [f"# {principle} — Examples\n"]
    for f in sorted(ex_dir.iterdir()):
        if not f.is_file():
            continue
        label = _rel_label(f)
        tag = ""
        if "compliant" in f.stem:
            tag = " [compliant]"
        elif "violation" in f.stem:
            tag = " [violation]"
        elif "exception" in f.stem:
            tag = " [exception]"
        content = _read(f).rstrip()
        parts.append(f"## {label}{tag}\n\n```swift\n{content}\n```\n")

    return _maybe_chunk("\n".join(parts), f"examples-{principle}")


# ---------------------------------------------------------------------------
# Tool: load_pattern
# ---------------------------------------------------------------------------

@server.tool(
    name="load_pattern",
    description=(
        "Load a design pattern reference by name. Returns full content with frontmatter stripped. "
        "If the name is not found, returns a catalog of all available patterns."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Pattern name, e.g. 'strategy', 'facade', 'adapter', 'decorator'.",
            },
        },
        "required": ["name"],
    },
)
def load_pattern(name):
    if not PATTERNS_ROOT.is_dir():
        return "Design patterns directory not found."

    for f in PATTERNS_ROOT.glob("*/*.md"):
        if f.stem.lower() == name.lower():
            return f"# {f.stem.capitalize()} Pattern\n\n{_read(f)}"

    available = []
    for f in sorted(PATTERNS_ROOT.glob("*/*.md")):
        try:
            fm = parse_frontmatter.parse(str(f))
            display = fm.get("displayName") or fm.get("name") or f.stem
            desc = (fm.get("description") or "").strip()
            suffix = f" — {desc}" if desc else ""
            available.append(f"- **{display}**{suffix} (`{_rel_label(f)}`)")
        except Exception:
            available.append(f"- {f.stem} (`{_rel_label(f)}`)")

    catalog = "\n".join(available) if available else "(none)"
    return f"Pattern '{name}' not found.\n\nAvailable patterns:\n{catalog}"


if __name__ == "__main__":
    server.run()
