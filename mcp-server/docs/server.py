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

from rules import discover_principles
from spec import parse_frontmatter
from rules.load_reference import strip_frontmatter
from common.chunker import Chunker
from rules.principle_registry import PrincipleRegistry
from findings.fix_file_lookup import find_fix_file
from rules.rule_file_collector import collect_files
import modes as modes_module
from protocol import MCPServer

server = MCPServer("solid-coder-docs", "1.0.0")
_chunker = Chunker()
_registry = PrincipleRegistry(REFS_ROOT)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read(path) -> str:
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")
        return strip_frontmatter(raw)
    except OSError as e:
        return f"[could not read {path}: {e}]"


def _rel_label(path: Path) -> str:
    try:
        return str(path.relative_to(PLUGIN_ROOT))
    except ValueError:
        return path.name


_STRIP_HEADINGS = frozenset({"severity bands", "quantitative metrics summary"})


def _strip_review_only_sections(content: str) -> str:
    """Remove sections only relevant to review agents (severity thresholds).

    Strips:
    - Markdown headings in _STRIP_HEADINGS (and content until next `---`)
    - XML <severity-bands> blocks (open tag to closing </severity-bands>)
    Non-review modes need violation definitions and exceptions, not thresholds.
    """
    import re as _re
    # Strip XML severity-bands blocks first
    content = _re.sub(r"<severity-bands[^>]*>.*?</severity-bands>", "", content,
                      flags=_re.DOTALL)
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
    meta={"anthropic/maxResultSizeChars": 1000000},
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
        files = collect_files(
            folder=Path(p["folder"]),
            rule_path=p["rule_path"],
            exclude=exclude,
            profile=profile,
            parse_frontmatter=parse_frontmatter,
        )
        if files:
            blocks.append(_render_principle(p["name"], files, review_mode=mode == "review"))

    content = "\n\n---\n\n".join(blocks) if blocks else "No active principles found."
    return content


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
    all_p = _registry.all_principles()
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

    return "\n".join(parts)


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


# ---------------------------------------------------------------------------
# Tools: load_detection_rules, score_severity, load_fix_instructions
# Implemented in lib/gateway_tools.py; registered here for the docs server.
# ---------------------------------------------------------------------------

from lib.gateway_tools import make_gateway_handler as _make_gw

_gw = _make_gw(REFS_ROOT)


@server.tool(
    name="load_detection_rules",
    description=(
        "Load per-metric detection instructions and definitions for one or more principles. "
        "Pass principle name for a single principle, or matched_tags to get all active principles. "
        "Returns XML-block content (detection, definition, severity_bands, exceptions) when available, "
        "or full rule.md content as fallback for principles without XML blocks."
    ),
    meta={"anthropic/maxResultSizeChars": 1000000},
    input_schema={
        "type": "object",
        "properties": {
            "principle": {
                "type": "string",
                "description": "Principle name, e.g. 'SRP'. Omit to load all active principles.",
            },
            "matched_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags matched from the project. Filters conditional principles.",
            },
        },
    },
)
def load_detection_rules(principle=None, matched_tags=None):
    return _gw.load_detection_rules(principle=principle, matched_tags=matched_tags)


@server.tool(
    name="score_severity",
    description=(
        "Score an array of partial review output documents — one per active principle. "
        "Each document must have agent, principle, timestamp, and files[].units[].metrics filled. "
        "The MCP applies severity bands from rule.md XML deterministically and fills scoring + findings. "
        "No file is written. Used by the pre-write health check which activates multiple principles simultaneously."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "partial_outputs": {
                "type": "array",
                "description": "Array of partial output documents (one per principle) with metrics filled.",
                "items": {"type": "object"},
            },
        },
        "required": ["partial_outputs"],
    },
)
def score_severity(partial_outputs):
    return _gw.score_severity(partial_outputs)


@server.tool(
    name="load_fix_instructions",
    description=(
        "Load fix strategy text for a specific metric ID (e.g. 'SRP-1', 'OCP-2'). "
        "Returns the fix instructions from the principle's fix/ folder with frontmatter stripped. "
        "Returns an error message naming the unrecognised ID if not found."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "metric_id": {
                "type": "string",
                "description": "Metric ID, e.g. 'SRP-1', 'OCP-2', 'DRY-3'.",
            },
        },
        "required": ["metric_id"],
    },
)
def load_fix_instructions(metric_id):
    return _gw.load_fix_instructions(metric_id)


@server.tool(
    name="load_fix_instructions_for_findings",
    description=(
        "Load fix strategies for all findings in a file in one call. "
        "Pass the absolute path to the by-file validated findings JSON "
        "(e.g. {OUTPUT_ROOT}/by-file/SomeFile.swift.output.json). "
        "The tool reads the file, deduplicates by metric_id, searches all principle "
        "folders for the matching fix file, and returns all fix strategies concatenated. "
        "Works for any principle (SRP, OCP, SUI, TEST, etc.) — no principle field needed. "
        "Call once at the start of Phase 3. Use load_fix_for_violation for Phase 4 lookups."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "findings_path": {
                "type": "string",
                "description": "Absolute path to the by-file validated findings JSON.",
            },
        },
        "required": ["findings_path"],
    },
)
def load_fix_instructions_for_findings(findings_path):
    import json as _json
    try:
        raw = _json.loads(Path(findings_path).read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError) as e:
        return f"Could not read findings file '{findings_path}': {e}"

    metric_ids = []
    seen = set()
    for p in raw.get("principles", []):
        for f in p.get("findings", []):
            m = (f.get("metric") or f.get("metric_id") or "").strip().upper()
            if m and m not in seen:
                seen.add(m)
                metric_ids.append(m)
    for f in raw.get("findings", []):
        m = (f.get("metric_id") or f.get("metric") or "").strip().upper()
        if m and m not in seen:
            seen.add(m)
            metric_ids.append(m)

    all_p = _registry.all_principles()
    parts, missing = [], []
    for metric_id in metric_ids:
        p_entry, fix_path = find_fix_file(metric_id, all_p)
        if not fix_path:
            missing.append(f"no fix file for {metric_id}")
            continue
        content = _read(fix_path).rstrip()
        parts.append(f"# {p_entry['name'].upper()} — {metric_id} Fix Strategy\n\n## {_rel_label(fix_path)}\n\n{content}\n")

    result = "\n\n---\n\n".join(parts) if parts else ""
    if missing:
        result += ("\n\n" if result else "") + "> Note (fail-open): " + "; ".join(missing)
    return result or "No fix strategies found in the findings file."


@server.tool(
    name="load_fix_for_violation",
    description=(
        "Load fix strategies for one or more metric IDs in a single call. "
        "Pass ALL violation metric_ids at once — all strategies are returned concatenated. "
        "Searches all principle folders — works for any principle (SRP, OCP, SUI, TEST, SC, etc.). "
        "Call ONCE with the full list to avoid per-violation round trips."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "metric_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "One or more metric IDs, e.g. ['SRP-2', 'OCP-1']. Pass all at once.",
            },
        },
        "required": ["metric_ids"],
    },
)
def load_fix_for_violation(metric_ids, **_):
    if isinstance(metric_ids, str):
        metric_ids = [metric_ids]
    all_p = _registry.all_principles()
    available_cache = None
    parts = []
    for metric_id in metric_ids:
        norm = metric_id.strip().upper()
        p_entry, fix_path = find_fix_file(norm, all_p)
        if not fix_path:
            if available_cache is None:
                available_cache = sorted(
                    f.stem
                    for p in all_p
                    for f in (Path(p["folder"]) / "fix").glob("*.md")
                    if (Path(p["folder"]) / "fix").is_dir() and f.stem != "instructions"
                )
            parts.append(f"# {norm}\n\nNo fix file found. Available: {', '.join(available_cache)}")
        else:
            content = _read(fix_path).rstrip()
            parts.append(
                f"# {p_entry['name'].upper()} — {norm} Fix Strategy\n\n"
                f"## {_rel_label(fix_path)}\n\n{content}\n"
            )
    return "\n\n---\n\n".join(parts) if parts else "No metric IDs provided."


if __name__ == "__main__":
    server.run()
